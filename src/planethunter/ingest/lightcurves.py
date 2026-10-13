"""FITS (SPOC/TESS-SPOC) -> float32 Parquet conversion with metadata, and reading it back.

Layout: <data>/parquet/sector=0001/author=SPOC/tic_0000000261136679.parquet
Columns: time (float64, BTJD), flux, flux_err, sap_flux (float32, e-/s), quality (int32),
cadenceno (int64), mom_centr1, mom_centr2 (float32, pixel).
Metadata (JSON in the Parquet schema, key b"planethunter"): star, sector, camera, procver, sha256.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from astropy.io import fits

from planethunter.models import StarParams

META_KEY = b"planethunter"
_FNAME_RE = re.compile(r"tess\d+-s(?P<sector>\d{4})-(?P<tic>\d{16})-\d{4}-[a-z]_lc\.fits")


@dataclass(frozen=True)
class LightCurveMeta:
    tic_id: int
    sector: int
    author: str
    camera: int | None
    ccd: int | None
    procver: str
    data_release: int | None
    source_file: str
    sha256: str
    n_points: int
    star: StarParams

    def to_json(self) -> str:
        d = self.__dict__.copy()
        d["star"] = self.star.to_dict()
        return json.dumps(d)

    @classmethod
    def from_json(cls, blob: str | bytes) -> LightCurveMeta:
        d = json.loads(blob)
        d["star"] = StarParams(**d["star"])
        return cls(**d)


def parse_lc_filename(name: str) -> tuple[int, int] | None:
    """Extract (sector, tic_id) from the standard SPOC file name. None if it does not match."""
    m = _FNAME_RE.search(name)
    return (int(m["sector"]), int(m["tic"])) if m else None


def parquet_path(root: Path, sector: int, author: str, tic_id: int) -> Path:
    return (
        root
        / "parquet"
        / f"sector={sector:04d}"
        / f"author={author}"
        / f"tic_{tic_id:016d}.parquet"
    )


def _num(header: fits.Header, key: str) -> float | None:
    v = header.get(key)
    if v is None or isinstance(v, str | bool):
        return None
    v = float(v)
    return v if math.isfinite(v) else None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_spoc_fits(path: Path, author: str = "SPOC") -> tuple[pd.DataFrame, LightCurveMeta]:
    """Read a SPOC/TESS-SPOC *_lc.fits file. Does not apply the quality mask."""
    with fits.open(path, memmap=False) as hdul:
        h0, h1 = hdul[0].header, hdul[1].header
        d = hdul[1].data
        bjdrefi = h1.get("BJDREFI", 2457000)
        if bjdrefi != 2457000:
            raise ValueError(
                f"unexpected BJDREFI {bjdrefi} in {path.name}; expected 2457000 (BTJD)"
            )
        df = pd.DataFrame(
            {
                "time": np.asarray(d["TIME"], dtype=np.float64),
                "flux": np.asarray(d["PDCSAP_FLUX"], dtype=np.float32),
                "flux_err": np.asarray(d["PDCSAP_FLUX_ERR"], dtype=np.float32),
                "sap_flux": np.asarray(d["SAP_FLUX"], dtype=np.float32),
                "quality": np.asarray(d["QUALITY"], dtype=np.int32),
                "cadenceno": np.asarray(d["CADENCENO"], dtype=np.int64),
                "mom_centr1": np.asarray(d["MOM_CENTR1"], dtype=np.float32),
                "mom_centr2": np.asarray(d["MOM_CENTR2"], dtype=np.float32),
            }
        )
        tic_id = int(h0["TICID"])
        star = StarParams(
            tic_id=tic_id,
            ra_deg=_num(h0, "RA_OBJ"),
            dec_deg=_num(h0, "DEC_OBJ"),
            pmra_mas_yr=_num(h0, "PMRA"),
            pmdec_mas_yr=_num(h0, "PMDEC"),
            tmag=_num(h0, "TESSMAG"),
            teff_k=_num(h0, "TEFF"),
            logg_cgs=_num(h0, "LOGG"),
            radius_rsun=_num(h0, "RADIUS"),
            crowdsap=_num(h1, "CROWDSAP"),
        )
        meta = LightCurveMeta(
            tic_id=tic_id,
            sector=int(h0["SECTOR"]),
            author=author,
            camera=int(h0["CAMERA"]) if h0.get("CAMERA") is not None else None,
            ccd=int(h0["CCD"]) if h0.get("CCD") is not None else None,
            procver=str(h0.get("PROCVER", "")),
            data_release=int(h0["DATA_REL"]) if h0.get("DATA_REL") is not None else None,
            source_file=path.name,
            sha256=_sha256(path),
            n_points=len(df),
            star=star,
        )
    # Without a valid time there is nothing to do with the cadence.
    df = df[np.isfinite(df["time"].to_numpy())].reset_index(drop=True)
    meta = LightCurveMeta(**{**meta.__dict__, "n_points": len(df)})
    return df, meta


def write_parquet(df: pd.DataFrame, meta: LightCurveMeta, dest: Path) -> Path:
    """Atomic write with metadata in the schema."""
    if df.empty:
        raise ValueError(f"empty light curve for TIC {meta.tic_id} sector {meta.sector}")
    if not np.all(np.diff(df["time"].to_numpy()) > 0):
        raise ValueError(f"non-monotonic time for TIC {meta.tic_id} sector {meta.sector}")
    table = pa.Table.from_pandas(df, preserve_index=False)
    table = table.replace_schema_metadata(
        {**(table.schema.metadata or {}), META_KEY: meta.to_json()}
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".parquet.part")
    pq.write_table(table, tmp, compression="zstd")
    tmp.replace(dest)
    return dest


def read_parquet(path: Path) -> tuple[pd.DataFrame, LightCurveMeta]:
    table = pq.read_table(path)
    meta = LightCurveMeta.from_json(table.schema.metadata[META_KEY])
    return table.to_pandas(), meta


def fits_to_parquet(
    fits_path: Path, root: Path, author: str = "SPOC", delete_fits: bool = False
) -> tuple[Path, LightCurveMeta]:
    df, meta = read_spoc_fits(fits_path, author=author)
    dest = write_parquet(df, meta, parquet_path(root, meta.sector, author, meta.tic_id))
    if delete_fits:
        fits_path.unlink(missing_ok=True)
    return dest, meta
