"""Local mirrors of the catalogs of known objects.

Each sync downloads the source, checks the raw contract (expected columns, row count not
dropping > 10 %), normalizes it to a common schema and writes
<data>/mirrors/<source>/<UTC stamp>.parquet plus a manifest <UTC stamp>.json with
{source, file, synced_at, n_rows, sha256, version, url}. The crossmatch only reads these
files (no network in the batch path).

Common schema: source, name, tic_id (Int64), ra_deg, dec_deg, period_days, period_err_days,
t0_btjd, depth_ppm, disposition, synced_at (UTC ISO). Dispositions are normalized to
CP/KP (planet), PC/APC (candidate), FP/FA (false positive) and EB.

Sources and freshness (config `crossmatch.mirror_max_age_hours*`, `static_sources`):
- live, 48 h: ExoFOP TOI and CTOI (source of truth for TOI dispositions), Archive pscomppars;
- weekly: exoplanet.eu (all statuses: Confirmed -> CP, Retracted -> FP, others -> PC), K2
  planets and candidates (k2pandc, default parameter set);
- monthly: Kepler KOI cumulative table (frozen since DR25);
- static VizieR catalogs (presence + version + sha256): TESS EBs Prsa+2022, TESS Ten
  Thousand EBs Kostov+2025, DIAmante Montalto+2020, DTARPS-S Melton+2024, LEO-Vetter
  Kunimoto+2025, ExoMiner++ Valizadegan+2025 (PC dispositions and the 50 new CTOIs).
A static file whose manifest version differs from the code's `MirrorSpec.version` counts as
missing (re-sync needed). Files without a manifest (older syncs, tests) are accepted.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord

from planethunter.crossmatch.core import Source
from planethunter.log import get_logger

log = get_logger(__name__)

BTJD_OFFSET = 2457000.0
BKJD_OFFSET = 2454833.0  # Kepler BJD - 2454833
EXOFOP_TOI = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
EXOFOP_CTOI = "https://exofop.ipac.caltech.edu/tess/download_ctoi.php?sort=ctoi&output=csv"
ARCHIVE_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query="
EXOPLANET_EU = "https://exoplanet.eu/catalog/csv/"  # slow: minutes; no TIC, position only
TESS_EB_VIZIER = "J/ApJS/258/16/tess-ebs"  # Prsa+2022, 4584 EBs; BJD0 already in BTJD
ARCHIVE_QUERY = (
    "select pl_name, tic_id, ra, dec, pl_orbper, pl_orbpererr1, pl_tranmid, pl_trandep "
    "from pscomppars"
)
KOI_QUERY = (
    "select kepid, kepoi_name, kepler_name, ra, dec, koi_period, koi_period_err1, "
    "koi_time0bk, koi_depth, koi_disposition from cumulative"
)
K2_QUERY = (
    "select pl_name, tic_id, ra, dec, pl_orbper, pl_orbpererr1, pl_tranmid, pl_trandep, "
    "disposition from k2pandc where default_flag = 1"
)
KOSTOV_EB = ("J/ApJS/279/50/table3", "J/ApJS/279/50/table4")
DIAMANTE = "J/MNRAS/498/1726/table7"
DTARPS = ("J/AJ/167/203/table1", "J/AJ/167/203/table4")
LEO_VETTER = "J/AJ/170/280/table3"
EXOMINERPP = ("J/AJ/170/287/table13", "J/AJ/170/287/table16")

COLUMNS = [
    "source",
    "name",
    "tic_id",
    "ra_deg",
    "dec_deg",
    "period_days",
    "period_err_days",
    "t0_btjd",
    "depth_ppm",
    "disposition",
    "synced_at",
]


# ---------------------------------------------------------------- fetch (network)


def _fetch_csv(url: str) -> pd.DataFrame:
    """Whole CSV in memory. The requests timeout applies per read, not to the total."""
    from planethunter.net import get_with_retry

    text = get_with_retry(url, timeout=180).text
    return pd.read_csv(io.StringIO(text), low_memory=False)


def _fetch_vizier(catalog: str, columns: list[str], *, retries: int = 4) -> pd.DataFrame:
    """One VizieR table, whole. Timeout per request, exponential backoff between attempts."""
    from astroquery.vizier import Vizier

    last: Exception | None = None
    for attempt in range(retries):
        try:
            viz = Vizier(row_limit=-1, columns=columns)
            viz.TIMEOUT = 300
            tables = viz.get_catalogs(catalog)
            if not tables:
                raise RuntimeError(f"VizieR returned no result for {catalog}")
            return tables[0].to_pandas()
        except Exception as exc:  # network/HTTP errors from astroquery are heterogeneous
            last = exc
            log.warning("vizier retry", extra={"stage": catalog, "error": str(exc)[:200]})
            time.sleep(min(60.0, 2**attempt))
    raise RuntimeError(f"VizieR failed after {retries} attempts: {catalog}") from last


def _fetch_vizier_many(specs: list[tuple[str, list[str]]]) -> pd.DataFrame:
    frames = []
    for cat, cols in specs:
        df = _fetch_vizier(cat, cols)
        df["_table"] = cat
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- normalization (pure)


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _positive(s: pd.Series) -> pd.Series:
    s = _num(s)
    return s.where(s > 0)


def _bjd_to_btjd(s: pd.Series) -> pd.Series:
    s = _num(s)
    # Some sources already use BTJD or BJD-2454833; only values clearly in BJD are converted.
    return s.where(s < 2_000_000, s - BTJD_OFFSET)


def _ctoi_epoch_to_btjd(s: pd.Series, *, source: str = "ctoi") -> pd.Series:
    """CTOI epochs are user-entered: full BJD, BTJD, or BJD - 2400000 (audit B9: ~99 rows).

    >= 2e6: BJD; 4e4 < t < 7e4: BJD - 2400000 (subtract 57000). Anything that still lands
    outside -1e4 < BTJD < 1e4 (before ~1990 or after ~2042, e.g. CTOI-33840779.01 at
    BJD 2401427) is ambiguous and set to null (logged).
    """
    s = _bjd_to_btjd(s)
    rjd = (s > 4e4) & (s < 7e4)
    s = s.where(~rjd, s - 57000.0)
    bad = (s > 1e4) | (s < -1e4)
    if bad.any():
        log.warning("unrecognized epochs set to null", extra={"stage": source, "n": int(bad.sum())})
    return s.where(~bad)


def _tic_int(s: pd.Series) -> pd.Series:
    """'TIC 123', '0000123', 123.0 -> Int64 123 (never a string with a prefix)."""
    digits = s.astype(str).str.extract(r"(\d+)")[0]
    return _num(digits).astype("Int64")


def _empty_tic(n: int) -> pd.arrays.IntegerArray:
    return pd.array([pd.NA] * n, dtype="Int64")


def normalize_exofop_toi(df: pd.DataFrame) -> pd.DataFrame:
    coords = SkyCoord(df["RA"].astype(str), df["Dec"].astype(str), unit=(u.hourangle, u.deg))
    tfop = df["TFOPWG Disposition"].fillna("").astype(str).str.strip()
    tess = df["TESS Disposition"].fillna("").astype(str).str.strip()
    return pd.DataFrame(
        {
            "source": Source.TOI.value,
            "name": "TOI-" + df["TOI"].astype(str),
            "tic_id": _num(df["TIC ID"]).astype("Int64"),
            "ra_deg": coords.ra.deg,
            "dec_deg": coords.dec.deg,
            "period_days": _positive(df["Period (days)"]),
            "period_err_days": _positive(df["Period (days) err"]),
            "t0_btjd": _bjd_to_btjd(df["Epoch (BJD)"]),
            "depth_ppm": _num(df["Depth (ppm)"]),
            "disposition": tfop.where(tfop != "", tess),
        }
    )


def normalize_exofop_ctoi(df: pd.DataFrame) -> pd.DataFrame:
    tfop = df["TFOPWG Disposition"].fillna("").astype(str).str.strip()
    user = df["User Disposition"].fillna("").astype(str).str.strip()
    return pd.DataFrame(
        {
            "source": Source.CTOI.value,
            "name": "CTOI-" + df["CTOI"].astype(str),
            "tic_id": _num(df["TIC ID"]).astype("Int64"),
            "ra_deg": _num(df["RA"]),
            "dec_deg": _num(df["Dec"]),
            "period_days": _positive(df["Period (days)"]),
            "period_err_days": _positive(df["Period (days) Error"]),
            "t0_btjd": _ctoi_epoch_to_btjd(df["Transit Epoch (BJD)"]),
            "depth_ppm": _num(df["Depth ppm"]),
            "disposition": tfop.where(tfop != "", user),
        }
    )


def normalize_archive(df: pd.DataFrame) -> pd.DataFrame:
    # Archive pl_trandep is in %; convert to ppm.
    return pd.DataFrame(
        {
            "source": Source.ARCHIVE_PLANET.value,
            "name": df["pl_name"].astype(str),
            "tic_id": _tic_int(df["tic_id"]),
            "ra_deg": _num(df["ra"]),
            "dec_deg": _num(df["dec"]),
            "period_days": _positive(df["pl_orbper"]),
            "period_err_days": _positive(df["pl_orbpererr1"]),
            "t0_btjd": _bjd_to_btjd(df["pl_tranmid"]),
            "depth_ppm": _num(df["pl_trandep"]) * 1e4,
            "disposition": "CP",
        }
    )


EU_STATUS = {"confirmed": "CP", "retracted": "FP"}  # Candidate/Controversial/... -> PC


def normalize_exoplanet_eu(df: pd.DataFrame) -> pd.DataFrame:
    """All statuses are kept (Schneider+2011: inclusion is deliberately loose)."""
    if "planet_status" in df:
        status = df["planet_status"].fillna("Confirmed").astype(str).str.strip().str.lower()
        disp = status.map(EU_STATUS).fillna("PC")
    else:
        disp = pd.Series("CP", index=df.index)
    return pd.DataFrame(
        {
            "source": Source.EXOPLANET_EU.value,
            "name": df["name"].astype(str),
            "tic_id": _empty_tic(len(df)),  # catalog has no TIC
            "ra_deg": _num(df["ra"]),
            "dec_deg": _num(df["dec"]),
            "period_days": _positive(df["orbital_period"]),
            "period_err_days": _positive(_num(df["orbital_period_error_min"]).abs()),
            "t0_btjd": _bjd_to_btjd(df["tzero_tr"]),
            "depth_ppm": float("nan"),
            "disposition": disp.to_numpy(),
        }
    )


def normalize_tess_eb(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source": Source.EB_CATALOG.value,
            "name": "TESS-EB TIC " + df["TIC"].astype(str).str.lstrip("0"),
            "tic_id": _tic_int(df["TIC"]),
            "ra_deg": _num(df["RAJ2000"]),
            "dec_deg": _num(df["DEJ2000"]),
            "period_days": _positive(df["Per"]),
            "period_err_days": _positive(df["e_Per"]),
            "t0_btjd": _num(df["BJD0"]),  # catalog already uses BJD - 2457000
            "depth_ppm": float("nan"),
            "disposition": "EB",
        }
    )


KEPLER_DISP = {
    "CONFIRMED": "CP",
    "CANDIDATE": "PC",
    "FALSE POSITIVE": "FP",
    "REFUTED": "FP",
}


def normalize_koi(df: pd.DataFrame) -> pd.DataFrame:
    """Kepler KOI cumulative. Position only (no TIC); koi_time0bk is BJD - 2454833."""
    name = df["kepler_name"].where(df["kepler_name"].notna(), df["kepoi_name"]).astype(str)
    disp = df["koi_disposition"].fillna("").astype(str).str.upper().map(KEPLER_DISP)
    return pd.DataFrame(
        {
            "source": Source.KOI.value,
            "name": name + " (KIC " + df["kepid"].astype(str) + ")",
            "tic_id": _empty_tic(len(df)),
            "ra_deg": _num(df["ra"]),
            "dec_deg": _num(df["dec"]),
            "period_days": _positive(df["koi_period"]),
            "period_err_days": _positive(df["koi_period_err1"]),
            "t0_btjd": _num(df["koi_time0bk"]) + BKJD_OFFSET - BTJD_OFFSET,
            "depth_ppm": _num(df["koi_depth"]),
            "disposition": disp.fillna("PC").to_numpy(),
        }
    )


def normalize_k2(df: pd.DataFrame) -> pd.DataFrame:
    """K2 planets and candidates (default parameter set). pl_trandep in %."""
    disp = df["disposition"].fillna("").astype(str).str.upper().map(KEPLER_DISP)
    return pd.DataFrame(
        {
            "source": Source.K2.value,
            "name": df["pl_name"].astype(str),
            "tic_id": _tic_int(df["tic_id"]),
            "ra_deg": _num(df["ra"]),
            "dec_deg": _num(df["dec"]),
            "period_days": _positive(df["pl_orbper"]),
            "period_err_days": _positive(df["pl_orbpererr1"]),
            "t0_btjd": _bjd_to_btjd(df["pl_tranmid"]),
            "depth_ppm": _num(df["pl_trandep"]) * 1e4,
            "disposition": disp.fillna("PC").to_numpy(),
        }
    )


def normalize_kostov_eb(df: pd.DataFrame) -> pd.DataFrame:
    """Kostov+2025 table3 (7936 new EBs) + table4 (known EBs, TESS-measured period/T0)."""
    per = _num(df["Per"]) if "Per" in df else pd.Series(np.nan, index=df.index)
    t0 = _num(df["T0-pri"]) if "T0-pri" in df else pd.Series(np.nan, index=df.index)
    if "Per-TESS" in df:
        per = per.fillna(_num(df["Per-TESS"]))
        t0 = t0.fillna(_num(df["T0-TESS"]))
    tic = _tic_int(df["TIC"])
    return pd.DataFrame(
        {
            "source": Source.EB_KOSTOV2025.value,
            "name": "TTEB TIC " + tic.astype(str),
            "tic_id": tic,
            "ra_deg": _num(df["RAJ2000"]),
            "dec_deg": _num(df["DEJ2000"]),
            "period_days": per.where(per > 0),
            "period_err_days": np.nan,
            "t0_btjd": t0,  # BTJD
            "depth_ppm": np.nan,
            "disposition": "EB",
        }
    )


def normalize_diamante(df: pd.DataFrame) -> pd.DataFrame:
    """DIAmante (Montalto+2020): PBLS period, t0fit in BTJD, trdepth in ppm."""
    tic = _tic_int(df["TIC"])
    return pd.DataFrame(
        {
            "source": Source.PUB_DIAMANTE.value,
            "name": "DIAmante TIC " + tic.astype(str),
            "tic_id": tic,
            "ra_deg": _num(df["RA_ICRS"]),
            "dec_deg": _num(df["DE_ICRS"]),
            "period_days": _positive(df["PBLS"]),
            "period_err_days": np.nan,
            "t0_btjd": _num(df["t0fit"]),
            "depth_ppm": _num(df["trdepth"]),
            "disposition": "PC",
        }
    )


def normalize_dtarps(df: pd.DataFrame) -> pd.DataFrame:
    """DTARPS-S (Melton+2024) candidates + Galactic-plane list. T0 BTJD, Depth fractional."""
    tic = _tic_int(df["TIC"])
    return pd.DataFrame(
        {
            "source": Source.PUB_DTARPS.value,
            "name": "DTARPS TIC " + tic.astype(str),
            "tic_id": tic,
            "ra_deg": _num(df["RA_ICRS"]),
            "dec_deg": _num(df["DE_ICRS"]),
            "period_days": _positive(df["Period"]),
            "period_err_days": _positive(df["e_Period"]),
            "t0_btjd": _num(df["T0"]),
            "depth_ppm": _num(df["Depth"]) * 1e6,
            "disposition": "PC",
        }
    )


def normalize_leo_vetter(df: pd.DataFrame) -> pd.DataFrame:
    """LEO-Vetter (Kunimoto+2025) 172 PCs passing flux- and pixel-level vetting. T0 BTJD."""
    tic = _tic_int(df["TIC"])
    return pd.DataFrame(
        {
            "source": Source.PUB_LEO_VETTER.value,
            "name": "LEO-Vetter TIC " + tic.astype(str),
            "tic_id": tic,
            "ra_deg": _num(df["_RA"]),
            "dec_deg": _num(df["_DE"]),
            "period_days": _positive(df["Per"]),
            "period_err_days": _positive(df["e_Per"]),
            "t0_btjd": _num(df["T0"]),
            "depth_ppm": _num(df["Rp/Rs"]) ** 2 * 1e6,
            "disposition": "PC",
        }
    )


def normalize_exominerpp(df: pd.DataFrame) -> pd.DataFrame:
    """ExoMiner++ (Valizadegan+2025): TCEs labeled PC (table13) and the 50 new CTOIs.

    One row per (TIC, TCE number), keeping the highest score. No epoch is published, so these
    objects only match by period alias (conservatively, at any phase).
    """
    df = df.copy()
    if "ELab" in df:
        lab = df["ELab"].fillna("").astype(str).str.strip().str.upper()
        df = df[(lab == "PC") | (df["_table"] == EXOMINERPP[1])]
    df["_score"] = _num(df["EScore"])
    df["TIC"] = _tic_int(df["TIC"])
    df = df.sort_values("_score", ascending=False).drop_duplicates(["TIC", "Num"])
    tic = df["TIC"]
    return pd.DataFrame(
        {
            "source": Source.PUB_EXOMINERPP.value,
            "name": "ExoMiner++ TIC " + tic.astype(str) + "." + df["Num"].astype(str),
            "tic_id": tic.to_numpy(),
            "ra_deg": _num(df["_RA"]).to_numpy(),
            "dec_deg": _num(df["_DE"]).to_numpy(),
            "period_days": _positive(df["Per"]).to_numpy(),
            "period_err_days": np.nan,
            "t0_btjd": np.nan,
            "depth_ppm": np.nan,
            "disposition": "PC",
        }
    )


# ---------------------------------------------------------------- specs


@dataclass(frozen=True)
class MirrorSpec:
    """How to sync one source. `version` changes whenever the query/normalization changes;
    static catalogs are re-synced only when it changes (or with --force)."""

    fetch: Callable[[], pd.DataFrame]
    normalize: Callable[[pd.DataFrame], pd.DataFrame]
    required_columns: tuple[str, ...]
    version: str
    url: str
    min_rows: int = 100


def _tap(query: str) -> str:
    return ARCHIVE_TAP + urllib.parse.quote(query)


_KOSTOV_COLS = [
    ["TIC", "RAJ2000", "DEJ2000", "Per", "T0-pri"],
    ["TIC", "RAJ2000", "DEJ2000", "Per-TESS", "T0-TESS"],
]
_DTARPS_COLS = ["TIC", "RA_ICRS", "DE_ICRS", "Period", "e_Period", "T0", "Depth"]
_EXOMINER_COLS = [
    ["TIC", "Num", "Per", "EScore", "ELab", "_RA", "_DE"],
    ["TIC", "Num", "Per", "EScore", "_RA", "_DE"],
]

SPECS: dict[Source, MirrorSpec] = {
    Source.TOI: MirrorSpec(
        lambda: _fetch_csv(EXOFOP_TOI),
        normalize_exofop_toi,
        ("TIC ID", "TOI", "RA", "Dec", "Period (days)", "Epoch (BJD)", "TFOPWG Disposition"),
        "exofop-toi-v1",
        EXOFOP_TOI,
    ),
    Source.CTOI: MirrorSpec(
        lambda: _fetch_csv(EXOFOP_CTOI),
        normalize_exofop_ctoi,
        ("TIC ID", "CTOI", "RA", "Dec", "Period (days)", "Transit Epoch (BJD)"),
        "exofop-ctoi-v2",  # v2: BJD-2400000 epochs normalized
        EXOFOP_CTOI,
    ),
    Source.ARCHIVE_PLANET: MirrorSpec(
        lambda: _fetch_csv(_tap(ARCHIVE_QUERY)),
        normalize_archive,
        ("pl_name", "tic_id", "ra", "dec", "pl_orbper", "pl_tranmid"),
        "pscomppars-v1",
        _tap(ARCHIVE_QUERY),
    ),
    Source.EXOPLANET_EU: MirrorSpec(
        lambda: _fetch_csv(EXOPLANET_EU),
        normalize_exoplanet_eu,
        ("name", "planet_status", "ra", "dec", "orbital_period", "tzero_tr"),
        "exoplanet-eu-v2",  # v2: all statuses kept
        EXOPLANET_EU,
    ),
    Source.EB_CATALOG: MirrorSpec(
        lambda: _fetch_vizier(
            TESS_EB_VIZIER, ["TIC", "RAJ2000", "DEJ2000", "BJD0", "Per", "e_Per", "Morph"]
        ),
        normalize_tess_eb,
        ("TIC", "RAJ2000", "DEJ2000", "BJD0", "Per"),
        TESS_EB_VIZIER,
        f"vizier:{TESS_EB_VIZIER}",
    ),
    Source.KOI: MirrorSpec(
        lambda: _fetch_csv(_tap(KOI_QUERY)),
        normalize_koi,
        ("kepid", "kepoi_name", "ra", "dec", "koi_period", "koi_time0bk", "koi_disposition"),
        "koi-cumulative-v1",
        _tap(KOI_QUERY),
    ),
    Source.K2: MirrorSpec(
        lambda: _fetch_csv(_tap(K2_QUERY)),
        normalize_k2,
        ("pl_name", "tic_id", "ra", "dec", "pl_orbper", "pl_tranmid", "disposition"),
        "k2pandc-v1",
        _tap(K2_QUERY),
    ),
    Source.EB_KOSTOV2025: MirrorSpec(
        lambda: _fetch_vizier_many(list(zip(KOSTOV_EB, _KOSTOV_COLS, strict=True))),
        normalize_kostov_eb,
        ("TIC", "RAJ2000", "DEJ2000"),
        "+".join(KOSTOV_EB),
        "vizier:" + "+".join(KOSTOV_EB),
    ),
    Source.PUB_DIAMANTE: MirrorSpec(
        lambda: _fetch_vizier(
            DIAMANTE, ["TIC", "RA_ICRS", "DE_ICRS", "PBLS", "t0fit", "Duration", "trdepth"]
        ),
        normalize_diamante,
        ("TIC", "RA_ICRS", "DE_ICRS", "PBLS", "t0fit"),
        DIAMANTE,
        f"vizier:{DIAMANTE}",
    ),
    Source.PUB_DTARPS: MirrorSpec(
        lambda: _fetch_vizier_many([(t, _DTARPS_COLS) for t in DTARPS]),
        normalize_dtarps,
        tuple(_DTARPS_COLS),
        "+".join(DTARPS),
        "vizier:" + "+".join(DTARPS),
    ),
    Source.PUB_LEO_VETTER: MirrorSpec(
        lambda: _fetch_vizier(LEO_VETTER, ["TIC", "Per", "e_Per", "T0", "Rp/Rs", "_RA", "_DE"]),
        normalize_leo_vetter,
        ("TIC", "Per", "T0", "_RA", "_DE"),
        LEO_VETTER,
        f"vizier:{LEO_VETTER}",
    ),
    Source.PUB_EXOMINERPP: MirrorSpec(
        lambda: _fetch_vizier_many(list(zip(EXOMINERPP, _EXOMINER_COLS, strict=True))),
        normalize_exominerpp,
        ("TIC", "Num", "Per", "_RA", "_DE"),
        "+".join(EXOMINERPP) + ":PC",
        "vizier:" + "+".join(EXOMINERPP),
    ),
}


# ---------------------------------------------------------------- sync and load


def mirror_dir(root: Path, source: Source) -> Path:
    return root / "mirrors" / source.value


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_contract(source: Source, raw: pd.DataFrame) -> None:
    """Daily contract test on the raw download: expected columns exist."""
    missing = [c for c in SPECS[source].required_columns if c not in raw.columns]
    if missing:
        raise RuntimeError(f"mirror {source.value}: expected columns missing: {missing}")


def sync_source(root: Path, source: Source, *, min_rows: int | None = None) -> Path:
    """Download, check, normalize and write a mirror + manifest. Rejects suspicious results
    (missing columns, too few rows, or a drop > 10 % vs the previous mirror)."""
    spec = SPECS[source]
    now = datetime.now(UTC)
    raw = spec.fetch()
    check_contract(source, raw)
    df = spec.normalize(raw)
    floor = spec.min_rows if min_rows is None else min_rows
    if len(df) < floor:
        raise RuntimeError(
            f"mirror {source.value} has only {len(df)} rows; keeping the previous one"
        )
    previous = latest_mirror(root, source)
    if previous is not None:
        n_prev = len(pd.read_parquet(previous[0], columns=["name"]))
        if len(df) < 0.9 * n_prev:
            raise RuntimeError(
                f"mirror {source.value} dropped from {n_prev} to {len(df)} rows (>10 %); "
                "keeping the previous one"
            )
    df["synced_at"] = now.isoformat(timespec="seconds")
    dest = mirror_dir(root, source) / f"{now:%Y%m%dT%H%M%SZ}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    df["tic_id"] = df["tic_id"].astype("Int64")
    df[COLUMNS].to_parquet(dest, index=False)
    manifest = {
        "source": source.value,
        "file": dest.name,
        "synced_at": now.isoformat(timespec="seconds"),
        "n_rows": int(len(df)),
        "sha256": _sha256(dest),
        "version": spec.version,
        "url": spec.url,
    }
    dest.with_suffix(".json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    log.info("mirror synced", extra={"stage": source.value, "n": len(df)})
    return dest


def sync_all(
    root: Path, *, sources: list[Source] | None = None, force: bool = False
) -> dict[Source, Path | str]:
    """Sync every source (or `sources`). Static catalogs already present with the expected
    version are skipped unless `force`. A failure in one does not stop the others."""
    from planethunter.config import load_config

    cfg = load_config().crossmatch
    manifest = mirror_manifest(root)
    out: dict[Source, Path | str] = {}
    for source in sources or list(SPECS):
        info = manifest.get(source)
        if (
            not force
            and cfg.max_age_hours(source.value) is None
            and info is not None
            and info.get("version_ok")
        ):
            out[source] = f"static, up to date ({info['file']})"
            continue
        try:
            out[source] = sync_source(root, source)
        except Exception as exc:
            log.error("sync failed", extra={"stage": source.value, "error": str(exc)})
            out[source] = f"ERROR: {exc}"
    return out


def latest_mirror(root: Path, source: Source) -> tuple[Path, datetime] | None:
    files = sorted(mirror_dir(root, source).glob("*.parquet"))
    if not files:
        return None
    ts = datetime.strptime(files[-1].stem, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    return files[-1], ts


def mirror_manifest(root: Path) -> dict[Source, dict]:
    """Provenance of the latest mirror of each present source.

    {source: {file, synced_at, n_rows, sha256, version, version_ok, age_hours}}. Files
    without a manifest (older syncs) get the checksum computed now and version None.
    """
    now = datetime.now(UTC)
    out: dict[Source, dict] = {}
    for source in Source:
        latest = latest_mirror(root, source)
        if latest is None:
            continue
        path, ts = latest
        side = path.with_suffix(".json")
        info: dict = {}
        if side.exists():
            try:
                info = json.loads(side.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                info = {}
        if "sha256" not in info:
            info["sha256"] = _sha256(path)
        if "n_rows" not in info:
            info["n_rows"] = int(len(pd.read_parquet(path, columns=["name"])))
        info.setdefault("file", path.name)
        info.setdefault("synced_at", ts.isoformat(timespec="seconds"))
        info.setdefault("version", None)
        spec = SPECS.get(source)
        info["version_ok"] = info["version"] is None or (
            spec is not None and info["version"] == spec.version
        )
        info["age_hours"] = (now - ts).total_seconds() / 3600.0
        out[source] = info
    return out


def load_known(root: Path) -> tuple[pd.DataFrame, dict[Source, float | None]]:
    """Union of the latest mirror of each source + age (h) of each source.

    Age None = missing, or a manifest whose version differs from the code's (re-sync needed).
    """
    now = datetime.now(UTC)
    frames, ages = [], {}
    for source in Source:
        latest = latest_mirror(root, source)
        if latest is None:
            ages[source] = None
            continue
        path, ts = latest
        ages[source] = (now - ts).total_seconds() / 3600.0
        side = path.with_suffix(".json")
        if side.exists() and source in SPECS:
            try:
                version = json.loads(side.read_text(encoding="utf-8")).get("version")
            except (OSError, ValueError):
                version = None
            if version is not None and version != SPECS[source].version:
                log.warning(
                    "mirror version mismatch; re-sync needed",
                    extra={"stage": source.value, "error": f"{version} != {SPECS[source].version}"},
                )
                ages[source] = None
        frames.append(pd.read_parquet(path))
    frames = [f for f in frames if len(f)]
    known = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLUMNS)
    known["tic_id"] = known["tic_id"].astype("Int64")
    return known, ages


CATALOG_MIRRORS_DDL = """
CREATE TABLE IF NOT EXISTS catalog_mirrors (
    source VARCHAR, file VARCHAR, synced_at TIMESTAMP, n_rows BIGINT, sha256 VARCHAR,
    version VARCHAR, max_age_hours DOUBLE, recorded_at TIMESTAMP,
    PRIMARY KEY (source, file)
)
"""


def record_catalog_mirrors(con, manifest: dict[Source, dict], cfg) -> None:
    """Upsert the provenance of the mirrors used by a crossmatch into `catalog_mirrors`.

    A crossmatch row links to its mirror files through checked_at (UTC) - age: the file of
    `source` is the one whose synced_at = checked_at - mirror_ages_json[source] hours.
    """
    con.execute(CATALOG_MIRRORS_DDL)
    now = datetime.now(UTC).replace(tzinfo=None)
    for source, info in manifest.items():
        synced = datetime.fromisoformat(str(info["synced_at"]).replace("Z", "+00:00"))
        if synced.tzinfo is not None:
            synced = synced.astimezone(UTC).replace(tzinfo=None)
        con.execute(
            "INSERT OR REPLACE INTO catalog_mirrors VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                source.value,
                info["file"],
                synced,
                int(info["n_rows"]),
                info["sha256"],
                info.get("version"),
                cfg.max_age_hours(source.value),
                now,
            ],
        )


def angular_sep_arcsec(ra1: float, dec1: float, ra2: np.ndarray, dec2: np.ndarray) -> np.ndarray:
    """Angular separation (haversine): degrees in, arcsec out."""
    r1, d1, r2, d2 = map(np.radians, (ra1, dec1, ra2, dec2))
    a = np.sin((d2 - d1) / 2) ** 2 + np.cos(d1) * np.cos(d2) * np.sin((r2 - r1) / 2) ** 2
    return np.degrees(2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))) * 3600.0
