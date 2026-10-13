import numpy as np
import pytest

from planethunter.ingest.lightcurves import (
    fits_to_parquet,
    parquet_path,
    parse_lc_filename,
    read_parquet,
)
from tests.conftest import synthetic_sector, write_spoc_fits


def test_parse_spoc_filename():
    name = "tess2018206045859-s0001-0000000261136679-0120-s_lc.fits"
    assert parse_lc_filename(name) == (1, 261136679)
    assert parse_lc_filename("https://x/?uri=mast:TESS/product/" + name) == (1, 261136679)
    assert parse_lc_filename("anything.fits") is None


def test_fits_to_parquet_roundtrip(tmp_path):
    df = synthetic_sector()
    df.loc[5, "time"] = np.nan  # cadence without time must be dropped
    fits_path = write_spoc_fits(tmp_path / "raw" / "x_lc.fits", df, tic_id=42, sector=3)
    dest, meta = fits_to_parquet(fits_path, tmp_path, delete_fits=True)
    assert dest == parquet_path(tmp_path, 3, "SPOC", 42)
    assert not fits_path.exists()
    out, meta2 = read_parquet(dest)
    assert meta2 == meta
    assert len(out) == len(df) - 1
    assert out["time"].dtype == np.float64 and out["flux"].dtype == np.float32
    assert meta.star.radius_rsun == pytest.approx(1.0)
    assert meta.star.mass_or_estimate() == pytest.approx(1.0, rel=0.01)  # from logg 4.44 and R=1
    assert meta.star.crowdsap == pytest.approx(0.99)
    assert len(meta.sha256) == 64
