from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from astropy.io import fits

from planethunter.config import Config


def box_transits(
    t: np.ndarray, period: float, t0: float, duration_d: float, depth: float
) -> np.ndarray:
    phase = ((t - t0 + 0.5 * period) % period) - 0.5 * period
    return np.where(np.abs(phase) < duration_d / 2, -depth, 0.0)


def synthetic_sector(
    *,
    t_start: float = 1325.0,
    days: float = 27.0,
    cadence_min: float = 2.0,
    noise: float = 400e-6,
    planets: tuple[tuple[float, float, float, float], ...] = ((3.7, 1326.3, 2.5 / 24, 1500e-6),),
    variability: float = 0.002,
    seed: int = 1,
) -> pd.DataFrame:
    """Synthetic sector with a downlink gap in the middle. planets = (P, T0, duration_d, depth)."""
    rng = np.random.default_rng(seed)
    t = np.arange(t_start, t_start + days, cadence_min / 1440)
    mid = t_start + days / 2
    t = t[(t < mid - 0.5) | (t > mid + 0.5)]
    f = 1 + variability * np.sin(2 * np.pi * t / 5.0) + rng.normal(0, noise, t.size)
    for p in planets:
        f += box_transits(t, *p)
    return pd.DataFrame(
        {
            "time": t,
            "flux": (f * 1000).astype("f4"),
            "flux_err": np.full(t.size, noise * 1000, "f4"),
            "quality": np.zeros(t.size, "i4"),
        }
    )


def write_spoc_fits(
    path: Path,
    df: pd.DataFrame,
    *,
    tic_id: int,
    sector: int,
    ra: float = 84.29,
    dec: float = -80.47,
) -> Path:
    """FITS with the same layout as a SPOC *_lc.fits (only the columns/headers we use)."""
    n = len(df)
    cols = [
        fits.Column("TIME", "D", array=df["time"].to_numpy()),
        fits.Column("CADENCENO", "J", array=np.arange(n)),
        fits.Column("SAP_FLUX", "E", array=df["flux"].to_numpy()),
        fits.Column("SAP_FLUX_ERR", "E", array=df["flux_err"].to_numpy()),
        fits.Column("PDCSAP_FLUX", "E", array=df["flux"].to_numpy()),
        fits.Column("PDCSAP_FLUX_ERR", "E", array=df["flux_err"].to_numpy()),
        fits.Column("QUALITY", "J", array=df["quality"].to_numpy()),
        fits.Column("MOM_CENTR1", "E", array=np.full(n, 1000.0)),
        fits.Column("MOM_CENTR2", "E", array=np.full(n, 500.0)),
    ]
    h0 = fits.Header()
    h0.update(
        TICID=tic_id,
        SECTOR=sector,
        CAMERA=4,
        CCD=2,
        PROCVER="spoc-test",
        DATA_REL=1,
        TESSMAG=9.0,
        TEFF=5800.0,
        LOGG=4.44,
        RADIUS=1.0,
        RA_OBJ=ra,
        DEC_OBJ=dec,
        PMRA=10.0,
        PMDEC=-5.0,
    )
    h1 = fits.BinTableHDU.from_columns(cols)
    h1.header["BJDREFI"] = 2457000
    h1.header["CROWDSAP"] = 0.99
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.HDUList([fits.PrimaryHDU(header=h0), h1]).writeto(path, overwrite=True)
    return path


@pytest.fixture
def cfg() -> Config:
    return Config()
