"""Tests with real MAST data. Run with: uv run pytest -m network"""

import pytest

from planethunter.config import Config
from planethunter.db.store import connect
from planethunter.ingest.mast import ingest_target
from planethunter.pipeline import discover, run_search

PI_MEN = 261136679  # Pi Men c: P = 6.2679 d, ~300 ppm, TOI-144.01


@pytest.mark.network
def test_pi_men_c_recovered_in_sector_1(tmp_path):
    rep = ingest_target(PI_MEN, tmp_path, sectors=[1])
    assert not rep.errors and len(discover(tmp_path, tic_ids={PI_MEN})) == 1
    s = run_search(tmp_path, Config(), tic_ids={PI_MEN}, all_sectors=True, workers=1)
    con = connect(tmp_path)
    periods = [
        r[0]
        for r in con.execute(
            "SELECT period_days FROM signals WHERE run_id = ? AND sde >= 9", [s.run_id]
        ).fetchall()
    ]
    con.close()
    assert any(abs(p - 6.2679) / 6.2679 < 0.01 for p in periods), periods
