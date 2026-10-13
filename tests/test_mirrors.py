import pandas as pd
import pytest

from planethunter.catalogs.mirrors import (
    angular_sep_arcsec,
    normalize_archive,
    normalize_exofop_ctoi,
    normalize_exofop_toi,
)


def test_normalize_exofop_toi_real_columns():
    raw = pd.DataFrame(
        {
            "TIC ID": [231663901],
            "TOI": [101.01],
            "TFOPWG Disposition": [""],
            "TESS Disposition": ["KP"],
            "RA": ["21:14:56.88"],
            "Dec": ["-55:52:18.71"],
            "Period (days)": [1.43036994965074],
            "Period (days) err": [7.7e-7],
            "Epoch (BJD)": [2458326.009117],
            "Depth (ppm)": [18960.7],
        }
    )
    n = normalize_exofop_toi(raw).iloc[0]
    assert n["tic_id"] == 231663901 and n["name"] == "TOI-101.01"
    assert n["disposition"] == "KP"  # falls back to TESS Disposition when TFOPWG is empty
    assert n["ra_deg"] == pytest.approx(318.737, abs=1e-3)
    assert n["dec_deg"] == pytest.approx(-55.8719, abs=1e-3)
    assert n["t0_btjd"] == pytest.approx(1326.009117)


def test_normalize_ctoi_and_archive():
    ctoi = pd.DataFrame(
        {
            "TIC ID": [17361],
            "CTOI": [17361.01],
            "TFOPWG Disposition": [None],
            "User Disposition": ["PC"],
            "RA": [219.336233],
            "Dec": [-24.958522],
            "Period (days)": [3.60677],
            "Period (days) Error": [0.00023],
            "Transit Epoch (BJD)": [2458596.9598],
            "Depth ppm": [10036],
        }
    )
    c = normalize_exofop_ctoi(ctoi).iloc[0]
    assert c["disposition"] == "PC" and c["t0_btjd"] == pytest.approx(1596.9598)
    arch = pd.DataFrame(
        {
            "pl_name": ["HAT-P-8 b"],
            "tic_id": ["TIC 188876052"],
            "ra": [343.04],
            "dec": [35.44],
            "pl_orbper": [3.07634],
            "pl_orbpererr1": [4e-6],
            "pl_tranmid": [2456052.75596],
            "pl_trandep": [1.2],
        }
    )
    a = normalize_archive(arch).iloc[0]
    assert a["tic_id"] == 188876052 and a["depth_ppm"] == pytest.approx(12000)
    assert a["t0_btjd"] == pytest.approx(-947.24404)  # before TESS: negative BTJD is valid


def test_normalize_exoplanet_eu_and_eb():
    from planethunter.catalogs.mirrors import normalize_exoplanet_eu, normalize_tess_eb

    eu = pd.DataFrame(
        {
            "name": ["55 Cnc Ae"],
            "planet_status": ["Confirmed"],
            "ra": [133.149],
            "dec": [28.33],
            "orbital_period": [0.736546],
            "orbital_period_error_min": [1e-6],
            "tzero_tr": [2455962.0697],
        }
    )
    e = normalize_exoplanet_eu(eu).iloc[0]
    assert pd.isna(e["tic_id"]) and e["t0_btjd"] == pytest.approx(-1037.9303)
    eb = pd.DataFrame(
        {
            "TIC": ["0185259483"],
            "RAJ2000": [1.0],
            "DEJ2000": [2.0],
            "BJD0": [1544.164633],
            "Per": [0.310564],
            "e_Per": [1e-6],
        }
    )
    b = normalize_tess_eb(eb).iloc[0]
    assert b["tic_id"] == 185259483 and b["t0_btjd"] == pytest.approx(1544.164633)
    assert b["disposition"] == "EB"


def test_angular_separation():
    import numpy as np

    sep = angular_sep_arcsec(10.0, 20.0, np.array([10.0, 10.0]), np.array([20.0, 20.01]))
    assert sep[0] == pytest.approx(0.0) and sep[1] == pytest.approx(36.0, rel=1e-3)


# ---------------------------------------------------------------- 2026-10-10 audit additions


def test_ctoi_epochs_in_other_conventions_are_normalized():
    """Audit B9: ~99 CTOI epochs are in BJD - 2400000."""
    from planethunter.catalogs.mirrors import _ctoi_epoch_to_btjd

    s = _ctoi_epoch_to_btjd(
        pd.Series([2458596.96, 58596.96, 1596.96, 1_500_000.0, None, 2401427.0])
    )
    assert s.iloc[0] == pytest.approx(1596.96)
    assert s.iloc[1] == pytest.approx(1596.96)
    assert s.iloc[2] == pytest.approx(1596.96)
    assert pd.isna(s.iloc[3]) and pd.isna(s.iloc[4]) and pd.isna(s.iloc[5])


def test_exoplanet_eu_keeps_every_status():
    from planethunter.catalogs.mirrors import normalize_exoplanet_eu

    eu = pd.DataFrame(
        {
            "name": ["a", "b", "c", "d"],
            "planet_status": ["Confirmed", "Candidate", "Retracted", "Controversial"],
            "ra": [1.0] * 4,
            "dec": [2.0] * 4,
            "orbital_period": [3.0] * 4,
            "orbital_period_error_min": [-1e-4] * 4,
            "tzero_tr": [2459000.5] * 4,
        }
    )
    e = normalize_exoplanet_eu(eu)
    assert list(e["disposition"]) == ["CP", "PC", "FP", "PC"]
    assert e["period_err_days"].iloc[0] == pytest.approx(1e-4)


def test_normalize_koi_and_k2():
    from planethunter.catalogs.mirrors import normalize_k2, normalize_koi

    koi = pd.DataFrame(
        {
            "kepid": [10797460, 10811496],
            "kepoi_name": ["K00752.01", "K00753.01"],
            "kepler_name": ["Kepler-227 b", None],
            "ra": [291.93423, 297.00482],
            "dec": [48.141651, 48.134129],
            "koi_period": [9.48803557, 19.89913995],
            "koi_period_err1": [2.775e-05, 1.494e-05],
            "koi_time0bk": [170.53875, 175.850252],
            "koi_depth": [615.8, 10829.0],
            "koi_disposition": ["CONFIRMED", "FALSE POSITIVE"],
        }
    )
    k = normalize_koi(koi)
    assert list(k["disposition"]) == ["CP", "FP"]
    assert k["name"].iloc[0] == "Kepler-227 b (KIC 10797460)"
    assert k["name"].iloc[1].startswith("K00753.01")
    assert k["t0_btjd"].iloc[0] == pytest.approx(170.53875 + 2454833 - 2457000)
    assert k["tic_id"].isna().all()
    k2 = pd.DataFrame(
        {
            "pl_name": ["EPIC 203311200.01", "K2-42 b", "X"],
            "tic_id": ["TIC 67235717", "TIC 82054726", None],
            "ra": [240.97, 176.66, 1.0],
            "dec": [-26.55, -5.17, 1.0],
            "pl_orbper": [None, 6.68851, 2.0],
            "pl_orbpererr1": [None, 0.00074, None],
            "pl_tranmid": [2456954.01476, 2456814.6747, None],
            "pl_trandep": [0.3511, 0.1042, None],
            "disposition": ["CANDIDATE", "CONFIRMED", "REFUTED"],
        }
    )
    k = normalize_k2(k2)
    assert list(k["disposition"]) == ["PC", "CP", "FP"]
    assert k["tic_id"].iloc[0] == 67235717 and pd.isna(k["tic_id"].iloc[2])
    assert k["depth_ppm"].iloc[1] == pytest.approx(1042.0)


def test_normalize_vizier_catalogs():
    from planethunter.catalogs.mirrors import (
        EXOMINERPP,
        normalize_diamante,
        normalize_dtarps,
        normalize_exominerpp,
        normalize_kostov_eb,
        normalize_leo_vetter,
    )

    kost = pd.DataFrame(
        {
            "TIC": [8636, 10507],
            "RAJ2000": [219.0, 219.04],
            "DEJ2000": [-27.57, -24.33],
            "Per": [3.886554, None],
            "T0-pri": [1603.2923, None],
            "Per-TESS": [None, 1.939769],
            "T0-TESS": [None, 2359.1521],
        }
    )
    k = normalize_kostov_eb(kost)
    assert list(k["period_days"]) == pytest.approx([3.886554, 1.939769])
    assert list(k["t0_btjd"]) == pytest.approx([1603.2923, 2359.1521])
    assert set(k["disposition"]) == {"EB"} and k["tic_id"].iloc[1] == 10507
    d = normalize_diamante(
        pd.DataFrame(
            {
                "TIC": [282502866],
                "RA_ICRS": [90.08],
                "DE_ICRS": [1.79],
                "PBLS": [7.40066],
                "t0fit": [1462.4236],
                "trdepth": [13455],
            }
        )
    )
    assert d["period_days"].iloc[0] == pytest.approx(7.40066) and d["disposition"].iloc[0] == "PC"
    t = normalize_dtarps(
        pd.DataFrame(
            {
                "TIC": [17361],
                "RA_ICRS": [219.3],
                "DE_ICRS": [-24.9],
                "Period": [3.60667],
                "e_Period": [0.00038],
                "T0": [1600.57],
                "Depth": [0.0111],
            }
        )
    )
    assert t["depth_ppm"].iloc[0] == pytest.approx(11100.0)
    lv = normalize_leo_vetter(
        pd.DataFrame(
            {
                "TIC": [4487172],
                "Per": [24.12953],
                "e_Per": [4e-4],
                "T0": [1853.315],
                "Rp/Rs": [0.0706],
                "_RA": [117.06],
                "_DE": [32.18],
            }
        )
    )
    assert lv["depth_ppm"].iloc[0] == pytest.approx(0.0706**2 * 1e6)
    em = pd.DataFrame(
        {
            "TIC": [1, 1, 2, 3],
            "Num": [1, 1, 1, 1],
            "Per": [0.9263, 0.9264, 3.0, 5.0],
            "EScore": [0.99, 0.98, 0.2, 0.95],
            "ELab": ["PC", "PC", "AFP", None],
            "_RA": [1.0, 1.0, 2.0, 3.0],
            "_DE": [1.0, 1.0, 2.0, 3.0],
            "_table": [EXOMINERPP[0]] * 3 + [EXOMINERPP[1]],
        }
    )
    e = normalize_exominerpp(em)
    assert sorted(e["tic_id"].tolist()) == [1, 3]  # deduplicated, non-PC dropped, new CTOIs kept
    assert e["t0_btjd"].isna().all()


def test_contract_and_sync_with_manifest(tmp_path, monkeypatch):
    import json

    from planethunter.catalogs import mirrors as m
    from planethunter.crossmatch.core import Source

    raw = pd.DataFrame(
        {
            "TIC": range(1, 201),
            "Per": [3.0] * 200,
            "e_Per": [1e-4] * 200,
            "T0": [1500.0] * 200,
            "Rp/Rs": [0.1] * 200,
            "_RA": [10.0] * 200,
            "_DE": [0.0] * 200,
        }
    )
    spec = m.MirrorSpec(lambda: raw, m.normalize_leo_vetter, ("TIC", "Per"), "test-v1", "x")
    monkeypatch.setitem(m.SPECS, Source.PUB_LEO_VETTER, spec)
    dest = m.sync_source(tmp_path, Source.PUB_LEO_VETTER)
    man = json.loads(dest.with_suffix(".json").read_text(encoding="utf-8"))
    assert man["n_rows"] == 200 and man["version"] == "test-v1" and len(man["sha256"]) == 64
    info = m.mirror_manifest(tmp_path)[Source.PUB_LEO_VETTER]
    assert info["version_ok"] and info["sha256"] == man["sha256"]
    _, ages = m.load_known(tmp_path)
    assert ages[Source.PUB_LEO_VETTER] is not None
    # the code expects another catalog version: the mirror counts as missing
    monkeypatch.setitem(
        m.SPECS,
        Source.PUB_LEO_VETTER,
        m.MirrorSpec(lambda: raw, m.normalize_leo_vetter, ("TIC",), "test-v2", "x"),
    )
    _, ages = m.load_known(tmp_path)
    assert ages[Source.PUB_LEO_VETTER] is None
    # contract: a missing column is rejected before normalizing
    bad = m.MirrorSpec(
        lambda: raw.drop(columns=["Per"]), m.normalize_leo_vetter, ("Per",), "v", "x"
    )
    monkeypatch.setitem(m.SPECS, Source.PUB_LEO_VETTER, bad)
    with pytest.raises(RuntimeError, match="expected columns missing"):
        m.sync_source(tmp_path, Source.PUB_LEO_VETTER)


def test_sync_rejects_row_drop_and_skips_up_to_date_static(tmp_path, monkeypatch):
    from planethunter.catalogs import mirrors as m
    from planethunter.crossmatch.core import Source

    def raw(n):
        return pd.DataFrame(
            {
                "TIC": range(1, n + 1),
                "Per": [3.0] * n,
                "e_Per": [1e-4] * n,
                "T0": [1500.0] * n,
                "Rp/Rs": [0.1] * n,
                "_RA": [10.0] * n,
                "_DE": [0.0] * n,
            }
        )

    calls = []

    def fetch():
        calls.append(1)
        return raw(200 if len(calls) == 1 else 150)

    spec = m.MirrorSpec(fetch, m.normalize_leo_vetter, ("TIC",), "v1", "x")
    monkeypatch.setitem(m.SPECS, Source.PUB_LEO_VETTER, spec)
    out = m.sync_all(tmp_path, sources=[Source.PUB_LEO_VETTER])
    assert not str(out[Source.PUB_LEO_VETTER]).startswith("ERROR")
    out = m.sync_all(tmp_path, sources=[Source.PUB_LEO_VETTER])  # static and up to date
    assert "up to date" in str(out[Source.PUB_LEO_VETTER]) and len(calls) == 1
    out = m.sync_all(tmp_path, sources=[Source.PUB_LEO_VETTER], force=True)
    assert "dropped" in str(out[Source.PUB_LEO_VETTER])  # 200 -> 150 rows: kept the old one


def test_record_catalog_mirrors(tmp_path):
    import duckdb

    from planethunter.catalogs.mirrors import record_catalog_mirrors
    from planethunter.config import CrossmatchConfig
    from planethunter.crossmatch.core import Source

    con = duckdb.connect(str(tmp_path / "x.duckdb"))
    manifest = {
        Source.TOI: {
            "file": "20261010T000000Z.parquet",
            "synced_at": "2026-10-10T00:00:00+00:00",
            "n_rows": 8000,
            "sha256": "ab" * 32,
            "version": "exofop-toi-v1",
        }
    }
    record_catalog_mirrors(con, manifest, CrossmatchConfig())
    record_catalog_mirrors(con, manifest, CrossmatchConfig())  # idempotent
    rows = con.execute("SELECT source, n_rows, max_age_hours FROM catalog_mirrors").fetchall()
    assert rows == [("toi", 8000, 48.0)]
