"""Light curve download from MAST: per target (search via lightkurve) or whole sector (bulk).

Every function here touches the network: retry with backoff, disk cache, and a failure on one
target becomes an error row in the report, never a batch-wide exception.
"""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from planethunter.ingest.lightcurves import (
    LightCurveMeta,
    fits_to_parquet,
    parquet_path,
    parse_lc_filename,
)
from planethunter.log import get_logger
from planethunter.net import download_file, get_with_retry

log = get_logger(__name__)

MAST_DOWNLOAD = "https://mast.stsci.edu/api/v0.1/Download/file/?uri="
BULK_SCRIPT = (
    "https://archive.stsci.edu/missions/tess/download_scripts/sector/tesscurl_sector_{sector}_lc.sh"
)
_URL_RE = re.compile(r"(https://\S+_lc\.fits)")


@dataclass
class IngestReport:
    sector: int | None
    author: str
    ok: list[LightCurveMeta] = field(default_factory=list)
    skipped: list[int] = field(default_factory=list)  # already existed
    errors: list[tuple[str, str]] = field(default_factory=list)  # (url or tic, error)
    elapsed_s: float = 0.0

    def summary(self) -> dict:
        return {
            "sector": self.sector,
            "author": self.author,
            "ok": len(self.ok),
            "skipped": len(self.skipped),
            "errors": len(self.errors),
            "elapsed_s": round(self.elapsed_s, 1),
        }


def sector_lc_urls(sector: int) -> list[str]:
    """URLs of all SPOC 2-min light curves in the sector, from the MAST bulk script."""
    text = get_with_retry(BULK_SCRIPT.format(sector=sector), timeout=120).text
    return _URL_RE.findall(text)


def target_lc_urls(tic_id: int, author: str = "SPOC", exptime: int = 120) -> list[str]:
    """URLs of a target's light curves in every available sector."""
    import lightkurve as lk  # lazy import: slow and only needed here

    for attempt in range(4):
        try:
            sr = lk.search_lightcurve(
                f"TIC {tic_id}", mission="TESS", author=author, exptime=exptime
            )
            break
        except Exception as exc:  # astroquery raises assorted exception types
            if attempt == 3:
                raise
            log.warning("MAST search failed, retrying", extra={"tic_id": tic_id, "error": str(exc)})
            time.sleep(2**attempt)
    uris = [str(u) for u in sr.table["dataURI"]] if len(sr) else []
    return [MAST_DOWNLOAD + u for u in uris if u.endswith("_lc.fits")]


def _ingest_one(url: str, root: Path, author: str, keep_fits: bool) -> LightCurveMeta | int:
    name = url.rsplit("/", 1)[-1]  # ...?uri=mast:TESS/product/<name>_lc.fits
    parsed = parse_lc_filename(name)
    if parsed:
        sector, tic = parsed
        if parquet_path(root, sector, author, tic).exists():
            return tic
    fits_path = root / "raw" / name
    download_file(url, fits_path)
    _, meta = fits_to_parquet(fits_path, root, author=author, delete_fits=not keep_fits)
    return meta


def ingest_urls(
    urls: list[str],
    root: Path,
    *,
    sector: int | None = None,
    author: str = "SPOC",
    max_workers: int = 8,
    keep_fits: bool = False,
) -> IngestReport:
    """Download and convert in parallel (threads; I/O bound). Idempotent."""
    report = IngestReport(sector=sector, author=author)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_ingest_one, u, root, author, keep_fits): u for u in urls}
        for i, fut in enumerate(as_completed(futures), 1):
            url = futures[fut]
            try:
                res = fut.result()
            except Exception as exc:
                report.errors.append((url, f"{type(exc).__name__}: {exc}"))
                log.warning("ingest failed", extra={"sector": sector, "error": str(exc)})
                continue
            if isinstance(res, int):
                report.skipped.append(res)
            else:
                report.ok.append(res)
            if i % 500 == 0:
                log.info("ingest progress", extra={"sector": sector, "n": i})
    report.elapsed_s = time.perf_counter() - t0
    log.info("ingest finished", extra={"sector": sector, "author": author, **{"n": len(urls)}})
    return report


def ingest_sector(
    sector: int,
    root: Path,
    *,
    limit: int | None = None,
    tic_ids: set[int] | None = None,
    max_workers: int = 8,
    keep_fits: bool = False,
) -> IngestReport:
    """Ingest SPOC 2-min light curves for a sector. `tic_ids` filters; `limit` caps for tests."""
    urls = sector_lc_urls(sector)
    if tic_ids is not None:
        urls = [u for u in urls if (p := parse_lc_filename(u)) and p[1] in tic_ids]
    if limit is not None:
        urls = urls[:limit]
    return ingest_urls(urls, root, sector=sector, max_workers=max_workers, keep_fits=keep_fits)


def ingest_target(
    tic_id: int,
    root: Path,
    *,
    sectors: list[int] | None = None,
    author: str = "SPOC",
    keep_fits: bool = False,
) -> IngestReport:
    """Ingest all SPOC 2-min sectors of a target (or only `sectors`)."""
    urls = target_lc_urls(tic_id, author=author)
    if sectors:
        urls = [u for u in urls if (p := parse_lc_filename(u)) and p[0] in sectors]
    return ingest_urls(urls, root, author=author, max_workers=4, keep_fits=keep_fits)
