"""Offline end to end: synthetic FITS, Parquet, parallel search, crossmatch, candidates."""

from datetime import UTC, datetime

import pandas as pd

from planethunter.catalogs.mirrors import COLUMNS, mirror_dir
from planethunter.crossmatch import Source
from planethunter.db.store import connect
from planethunter.ingest.lightcurves import fits_to_parquet
from planethunter.pipeline import candidates, run_crossmatch, run_search
from tests.conftest import synthetic_sector, write_spoc_fits


def _write_mirrors(root, rows_by_source):
    ts = f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    for source in Source:
        df = pd.DataFrame(rows_by_source.get(source, []), columns=COLUMNS)
        df["tic_id"] = df["tic_id"].astype("Int64")
        d = mirror_dir(root, source)
        d.mkdir(parents=True, exist_ok=True)
        df.to_parquet(d / f"{ts}.parquet", index=False)


def test_end_to_end_known_vs_new(tmp_path, cfg):
    # Target 100: known planet (P=3.7). Target 200: uncatalogued planet (P=5.3).
    for tic, planet, ra in [
        (100, (3.7, 1326.3, 2.5 / 24, 2000e-6), 10.0),
        (200, (5.3, 1327.0, 3.0 / 24, 2000e-6), 50.0),
    ]:
        df = synthetic_sector(planets=(planet,), seed=tic)
        f = write_spoc_fits(
            tmp_path / "raw" / f"{tic}.fits", df, tic_id=tic, sector=1, ra=ra, dec=0.0
        )
        fits_to_parquet(f, tmp_path, delete_fits=True)

    known_row = dict(
        source=Source.TOI.value,
        name="TOI-9999.01",
        tic_id=100,
        ra_deg=10.0,
        dec_deg=0.0,
        period_days=3.7,
        period_err_days=1e-4,
        t0_btjd=1326.3,
        depth_ppm=2000.0,
        disposition="PC",
        synced_at="x",
    )
    _write_mirrors(tmp_path, {Source.TOI: [known_row]})

    summary = run_search(tmp_path, cfg, sector=1, workers=2)
    assert summary.n_done == 2 and summary.n_errors == 0

    con = connect(tmp_path)
    prov = con.execute(
        "SELECT DISTINCT run_id, pipeline_version, params_hash, sectors, author FROM signals"
    ).fetchall()
    con.close()
    assert len(prov) == 1 and all(prov[0])  # complete provenance

    xm = run_crossmatch(tmp_path, cfg, summary.run_id)
    assert set(xm["match_class"]) >= {"KNOWN_TOI", "NEW"}

    cands = candidates(tmp_path, cfg, summary.run_id)
    assert list(cands["tic_id"].unique()) == [200]
    assert abs(cands.iloc[0]["period_days"] - 5.3) / 5.3 < 0.01

    # Resume: rerunning with the same run_id reprocesses nothing.
    again = run_search(tmp_path, cfg, sector=1, workers=2, resume_run_id=summary.run_id)
    assert again.n_done == 2 and again.n_signals == summary.n_signals

    # Vetting, candidates, dossier and simulated alert.
    from planethunter.alerts.dossier import build_dossier
    from planethunter.alerts.notify import send_alerts
    from planethunter.pipeline import candidate_table, promote_candidates, run_vetting

    vet = run_vetting(tmp_path, cfg, summary.run_id, workers=2)
    assert len(vet) >= 2 and set(vet["verdict"]) <= {"PASS_BASIC", "FAIL"}
    promoted = promote_candidates(tmp_path, cfg, summary.run_id)
    assert list(promoted["tic_id"]) == [200]  # the known one (100) never becomes a candidate
    table = candidate_table(tmp_path, summary.run_id)
    assert table.iloc[0]["severity"] == "P1"  # clean; without deep vetting the ceiling is P1
    html_path = build_dossier(tmp_path, cfg, int(table.iloc[0]["signal_id"]))
    assert html_path.exists() and "TIC 200" in html_path.read_text(encoding="utf-8")
    first = send_alerts(tmp_path, cfg, summary.run_id, dry_run=True)
    assert [o.status for o in first] == ["dry_run"]
    again_alert = send_alerts(tmp_path, cfg, summary.run_id, dry_run=True)
    assert [o.status for o in again_alert] == ["skipped"]  # deduplicated
    assert list((tmp_path / "outbox").glob("*.md"))
