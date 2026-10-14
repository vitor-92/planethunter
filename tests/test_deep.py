"""Deep vetting with synthetic pixels and neighbors (no network)."""

import math

import numpy as np
import pandas as pd
import pytest

from planethunter.vetting.deep import PixelData, difference_image_test, neighbors_test

P, T0, DUR = 3.0, 1000.3, 0.12


def _psf(shape, x0, y0, sigma=1.0):
    yy, xx = np.indices(shape)
    return np.exp(-((xx - x0) ** 2 + (yy - y0) ** 2) / (2 * sigma**2))


def _pixels(source: str, seed: int = 0) -> PixelData:
    rng = np.random.default_rng(seed)
    t = np.arange(1000.0, 1027.0, 2 / 1440)
    shape = (11, 11)
    target, neighbor = _psf(shape, 5.0, 5.0), _psf(shape, 8.0, 5.0)
    ph = ((t - T0 + 0.5 * P) % P) - 0.5 * P
    dip = np.where(np.abs(ph) < DUR / 2, 1.0, 0.0)
    f_t = 10000 * (1 - (0.004 if source == "target" else 0) * dip)
    f_n = 2000 * (1 - (0.02 if source == "neighbor" else 0) * dip)
    cube = f_t[:, None, None] * target + f_n[:, None, None] * neighbor
    cube = cube + rng.normal(0, 3.0, cube.shape)
    ap = target > 0.2
    return PixelData(t, cube, np.ones(t.size, bool), ap, (5.0, 5.0), 1)


def test_transit_on_target_passes_difference_image():
    tr, info = difference_image_test(_pixels("target"), P, T0, DUR)
    assert tr.passed is True and tr.value < 0.3


def test_transit_on_neighbor_fails_difference_image():
    tr, _ = difference_image_test(_pixels("neighbor"), P, T0, DUR)
    assert tr.passed is False and tr.value > 1.0


def test_gaia_neighbors_rules():
    nb = pd.DataFrame({"sep_arcsec": [5.0, 40.0], "Tmag": [20.5, 12.0]})
    # 1000 ppm on a T=10 target: a T=20.5 neighbor would need >100 % -> impossible.
    # T=12 neighbor at 40": possible, but outside the 21" exclusion radius.
    tr = neighbors_test(nb, 10.0, 1000, exclusion_radius_arcsec=21.0)
    assert tr.passed is True
    close = pd.DataFrame({"sep_arcsec": [8.0], "Tmag": [13.0]})
    tr = neighbors_test(close, 10.0, 1000, exclusion_radius_arcsec=21.0)
    assert tr.passed is None and tr.value == 1.0 and "needs high-resolution imaging" in tr.note


def test_other_sectors_presence_and_veto():
    from planethunter.vetting.deep import other_sectors_test, sector_presence

    rng = np.random.default_rng(1)
    t = np.arange(2000.0, 2027.0, 2 / 1440)
    clean = 1 + rng.normal(0, 1000e-6, t.size)
    ph = ((t - 2001.0 + 3.3) % 6.6) - 3.3
    with_transit = clean - np.where(np.abs(ph) < 0.065, 4800e-6, 0.0)
    seen = sector_presence(t, with_transit, 6.6, 0.13, 4800)
    absent = sector_presence(t, clean, 6.6, 0.13, 4800)
    assert seen["snr"] > 7 and seen["expected_snr"] > 10
    assert absent["snr"] < 7
    assert other_sectors_test({1: seen, 2: absent}, 4800).passed is True
    veto = other_sectors_test({1: absent, 2: absent}, 4800)
    assert veto.veto and veto.passed is False


def test_simbad_suspect_types():
    from planethunter.vetting.deep import simbad_test

    # Only binaries fail; variables and young stars are informational (audit, Tier C).
    assert simbad_test(("V* AB Cas", "EB*")).passed is False
    assert simbad_test(("HD 1", "SB*")).passed is False
    assert simbad_test(("HD 2", "El*")).passed is False
    em = simbad_test(("LHA 120-S 18", "Em*"))
    assert em.passed is True and "informational" in em.note
    assert "informational" in simbad_test(("TYC 1", "Y*O")).note  # current code, not "YSO"
    assert simbad_test(("HD 271883", "PM*")).passed is True
    assert simbad_test(("TOI-431 b", "Pl")).passed is None  # the planet entry is not the star
    assert simbad_test(None).passed is None


def test_gaia_eb_and_depth_consistency():
    from planethunter.vetting.deep import gaia_eb_test, other_sectors_test

    ebs = pd.DataFrame({"Source": [1], "period_days": [13.2], "sep_arcsec": [3.0]})
    assert gaia_eb_test(ebs, 6.6).veto  # alias 1/2
    assert gaia_eb_test(pd.DataFrame(columns=["Source", "period_days", "sep_arcsec"]), 6.6).passed
    deep = {
        94: {"expected_snr": 37, "snr": 130, "depth_ppm": 63228},
        95: {"expected_snr": 32, "snr": 119, "depth_ppm": 67746},
    }
    assert other_sectors_test(deep, 13662).passed is False  # regression: signal 1748


def test_weak_recovery_in_other_sector_is_not_detection():
    """Regression, signal 1798: found SNR 19 and 26 where 46 and 64 were expected."""
    from planethunter.vetting.deep import other_sectors_test

    res = {
        67: {"expected_snr": 46, "snr": 19.2, "depth_ppm": 3118},
        97: {"expected_snr": 64, "snr": 26.0, "depth_ppm": 4226},
    }
    tr = other_sectors_test(res, 4872)
    assert tr.veto and tr.passed is False


def test_blind_recovery_and_floor_rules():
    """Regression, signal 1634: expected SNR below the noise floor is not a decisive absence."""
    from planethunter.vetting.deep import other_sectors_test

    weak = {
        95: {"expected_snr": 12, "snr": 12.4, "depth_ppm": 5061, "floor": 13.5},
        96: {"expected_snr": 9, "snr": 11.1, "depth_ppm": 5312, "floor": 11.6},
    }
    assert not other_sectors_test(weak, 5233).veto
    blind_no = {"recovered": False, "expected_total": 22, "note": "x"}
    assert other_sectors_test(weak, 5233, blind=blind_no).passed is False
    blind_yes = {"recovered": True, "expected_total": 22, "note": "x"}
    assert other_sectors_test(weak, 5233, blind=blind_yes).passed is True


def test_fpp_result_interpretation():
    from planethunter.alerts.severity import severity
    from planethunter.vetting.deep import fpp_test

    assert fpp_test({"ok": False, "error": "timeout"}).passed is None
    ok = fpp_test({"ok": True, "fpp": 0.35, "nfpp": 1e-9, "scenarios": []})
    assert ok.passed is True and "plausible" in ok.note
    assert fpp_test({"ok": True, "fpp": 0.9, "nfpp": 0.8, "scenarios": []}).veto
    assert "validation" in fpp_test({"ok": True, "fpp": 0.01, "nfpp": 1e-4, "scenarios": []}).note
    region = dict(nfpp=1e-4, rp_rearth=2.0, snr=20.0, two_min_cadence=True)
    assert severity("NEW", "PASS_BASIC", 0.9, deep_done=True, fpp=0.05, **region) == "P0"


def test_aperture_pixels_absolute_coordinates():
    pix = _pixels("target")
    pix.origin = (300, 1200)
    coords = pix.aperture_pixels()
    assert [305, 1205] in coords and all(c[0] >= 300 and c[1] >= 1200 for c in coords)


# ---------------------------------------------------------------- audit 2026-10-10


def test_difference_image_decides_on_catalog_position():
    """B4: a bright constant neighbor pulls the out-of-transit centroid, not the difference.

    Comparing with the out-of-transit centroid failed this target (10 of 20 s107 failures had
    the difference centroid within 1 px of the TIC position).
    """
    rng = np.random.default_rng(3)
    t = np.arange(1000.0, 1027.0, 2 / 1440)
    shape = (11, 11)
    ph = ((t - T0 + 0.5 * P) % P) - 0.5 * P
    dip = np.where(np.abs(ph) < DUR / 2, 1.0, 0.0)
    f_t = 3000 * (1 - 0.01 * dip)
    cube = f_t[:, None, None] * _psf(shape, 5.0, 5.0) + 20000 * _psf(shape, 7.0, 5.0)
    cube = cube + rng.normal(0, 3.0, cube.shape)
    pix = PixelData(t, cube, np.ones(t.size, bool), _psf(shape, 5, 5) > 0.2, (5.0, 5.0), 1)
    tr, info = difference_image_test(pix, P, T0, DUR)
    assert tr.passed is True and tr.value < 0.3
    assert math.hypot(info["c_diff"][0] - info["c_oot"][0], 0) > 1.0  # old rule would fail
    # Same scene, but the catalog position is wrong by 2 px (e.g. no proper-motion correction).
    pix.target_xy = (3.0, 5.0)
    tr, _ = difference_image_test(pix, P, T0, DUR)
    assert tr.passed is False and tr.extra["offset_significant"]


def test_difference_image_with_two_transits_is_indeterminate():
    pix = _pixels("neighbor")
    keep = pix.time < 1005.0  # 2 transits: no error estimate
    pix = PixelData(
        pix.time[keep], pix.flux[keep], pix.quality_ok[keep], pix.aperture, pix.target_xy, 1
    )
    tr, _ = difference_image_test(pix, P, T0, DUR)
    assert tr.passed is None and "indeterminate" in tr.note


def test_proper_motion_propagation():
    from planethunter.vetting.deep import btjd_to_jyear, match_gaia_target, propagate_position

    assert btjd_to_jyear(3000.0) == pytest.approx(2023.15, abs=0.01)
    ra, dec = propagate_position(10.0, 60.0, 1000.0, 1000.0, 2000.0, 2026.0)
    assert (dec - 60.0) * 3600 == pytest.approx(26.0, rel=1e-6)
    assert (ra - 10.0) * 3600 == pytest.approx(52.0, rel=1e-3)  # 26"/cos(60)
    assert propagate_position(10.0, 0.0, None, float("nan"), 2000.0, 2026.0) == (10.0, 0.0)
    # High proper motion: 300 mas/yr moves the star 4.8" between J2000 (TIC) and 2016 (Gaia).
    ra16, dec16 = propagate_position(150.0, 20.0, 0.0, 300.0, 2000.0, 2016.0)
    gaia = pd.DataFrame(
        {
            "Source": ["111", "222"],
            "RA_ICRS": [150.0, 150.0],
            "DE_ICRS": [dec16, 20.0 + 10 / 3600],
            "Gmag": [10.4, 15.0],
            "BP-RP": [0.8, 1.5],
            "pmRA": [0.0, 0.0],
            "pmDE": [300.0, 0.0],
        }
    )
    nb, t_target, note = match_gaia_target(gaia, 150.0, 20.0, pmdec_mas_yr=300.0, tmag=10.0)
    assert note == "" and t_target == pytest.approx(10.0, abs=0.2)
    assert list(nb["Source"]) == ["222"]
    _, _, note = match_gaia_target(gaia, 150.0, 20.0, tmag=10.0)  # without proper motion
    assert "not matched" in note


def test_gaia_to_tess_magnitude():
    from planethunter.vetting.deep import gaia_g_to_tmag

    assert gaia_g_to_tmag(np.array([10.0]), np.array([1.0]))[0] == pytest.approx(9.48243, abs=1e-4)
    assert gaia_g_to_tmag(np.array([10.0]))[0] == pytest.approx(9.57)
    assert gaia_g_to_tmag(np.array([10.0]), np.array([np.nan]))[0] == pytest.approx(9.57)


def test_neighbor_depth_uses_psf_in_aperture():
    """B7: needed depth = delta * F_target,ap / F_neighbor,ap (triceratops calc_depths)."""
    from planethunter.vetting.deep import psf_fraction_in_aperture

    ap = np.zeros((11, 11), bool)
    ap[4:7, 4:7] = True  # 3x3 around the target
    assert psf_fraction_in_aperture(5, 5, ap) == pytest.approx(0.9545**2, rel=1e-3)
    nb = pd.DataFrame(
        {"sep_arcsec": [42.0], "Tmag": [11.0], "x_px": [7.0], "y_px": [5.0], "Source": ["9"]}
    )
    tr = neighbors_test(
        nb, 10.0, 5000, exclusion_radius_arcsec=63.0, aperture=ap, target_xy=(5.0, 5.0)
    )
    f_t = psf_fraction_in_aperture(5, 5, ap) * 10 ** (-0.4 * 10)
    f_n = psf_fraction_in_aperture(7, 5, ap) * 10 ** (-0.4 * 11)
    expected = 5000e-6 * f_t / f_n
    assert expected < 1  # plausible -> needs imaging
    assert tr.passed is None and f"{expected:.0%}" in tr.note
    # The old formula (delta * F_total / F_neighbor, no PSF) underestimated it by ~2.7x here.
    rel = 10 ** (-0.4 * 1.0)
    assert expected / (5000e-6 * (1 + rel) / rel) > 2


def test_neighbor_at_difference_centroid_is_flagged():
    """G6: with a significant offset, a neighbor at the difference centroid is the likely source."""
    ap = np.zeros((11, 11), bool)
    ap[4:7, 4:7] = True
    nb = pd.DataFrame(
        {
            "sep_arcsec": [42.0, 30.0],
            "Tmag": [11.0, 18.0],
            "x_px": [7.0, 5.0],
            "y_px": [5.0, 6.4],
            "Source": ["4611686018427387905", "2"],
        }
    )
    kw = dict(exclusion_radius_arcsec=21.0, aperture=ap, target_xy=(5.0, 5.0), diff_xy=(7.1, 5.1))
    tr = neighbors_test(nb, 10.0, 2000, diff_offset_significant=True, **kw)
    assert tr.passed is False and "4611686018427387905" in tr.note
    assert tr.extra["at_difference_centroid"] == ["4611686018427387905"]
    tr = neighbors_test(nb, 10.0, 2000, diff_offset_significant=False, **kw)
    assert tr.passed is True and "near the difference centroid" in tr.note


def test_other_sectors_floor_does_not_scale_with_depth():
    """B3: the noise floor is measured with the signal masked (before: SNR 2192, floor 2272)."""
    from planethunter.vetting.deep import sector_presence

    rng = np.random.default_rng(5)
    t = np.arange(2000.0, 2027.0, 2 / 1440)
    noise = 1 + rng.normal(0, 1000e-6, t.size)
    ph = ((t - 2001.0 + 3.3) % 6.6) - 3.3
    box = np.where(np.abs(ph) < 0.065, 1.0, 0.0)
    shallow = sector_presence(t, noise - 3000e-6 * box, 6.6, 0.13, 3000, null_trials=30)
    deep = sector_presence(t, noise - 30000e-6 * box, 6.6, 0.13, 30000, null_trials=30)
    assert deep["snr"] > 5 * shallow["snr"]
    assert deep["floor"] < 1.5 * shallow["floor"]
    assert deep["floor"] < 0.1 * deep["snr"]


def test_gaia_eb_source_id_is_exact():
    from planethunter.vetting.deep import gaia_eb_test

    ebs = pd.DataFrame(
        {"Source": [np.int64(4611686018427387905)], "period_days": [5.0], "sep_arcsec": [2.0]}
    )
    tr = gaia_eb_test(ebs, 13.0)
    assert "4611686018427387905" in tr.note and "e+18" not in tr.note


def test_fpp_nfpp_rules_and_validation_region():
    """A4/Giacalone+2021: NFPP > 0.1 fails, > 0.5 vetoes; region flags stored in `extra`."""
    from planethunter.vetting.deep import fpp_test

    nearby = fpp_test({"ok": True, "fpp": 0.3, "nfpp": 0.24, "scenarios": []})
    assert nearby.passed is False and not nearby.veto and "nearby" in nearby.note
    region = dict(rp_rearth=2.5, snr=20.0, exptime_min=2.0)
    good = fpp_test({"ok": True, "fpp": 0.01, "nfpp": 1e-4, "scenarios": []}, **region)
    assert good.passed is True and good.extra["in_validation_region"] and good.extra["validated"]
    low_snr = fpp_test(
        {"ok": True, "fpp": 0.048, "nfpp": 1.6e-3, "scenarios": []}, **{**region, "snr": 8.0}
    )
    assert low_snr.extra["in_validation_region"] is False and not low_snr.extra["validated"]
    assert not low_snr.extra["likely_planet"]  # NFPP 1.6e-3 > 1e-3 (signal 4482)
    assert "outside the validation region" in low_snr.note
    ffi = fpp_test(
        {"ok": True, "fpp": 0.01, "nfpp": 0.0, "scenarios": []}, **{**region, "exptime_min": 30.0}
    )
    assert ffi.extra["cadence_ok"] is False and not ffi.extra["validated"]


def _run_fpp_module():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "tools" / "fpp" / "run_fpp.py"
    spec = importlib.util.spec_from_file_location("run_fpp_isolated", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FakeTarget:
    """Stand-in for triceratops.target with the attributes run_fpp uses."""

    def __init__(self, n_pix, stars, runs, degenerate=False):
        self.pix_coords = [np.zeros((2, 2))] * n_pix
        self.stars = stars
        self.runs = list(runs)
        self.degenerate = degenerate
        self.probs_calls: list[dict] = []
        self.depth_kw: dict = {}

    def calc_depths(self, **kw):
        self.depth_kw = kw

    def calc_probs(self, **kw):
        self.probs_calls.append(kw)
        self.FPP, self.NFPP = self.runs[len(self.probs_calls) - 1]
        self.FPP_degenerate = self.degenerate
        self.probs = pd.DataFrame({"scenario": ["TP", "EB"], "ID": [1, 1], "prob": [0.8, 0.2]})


def _fpp_cfg(tmp_path, **over):
    rng = np.random.default_rng(0)
    ph = np.linspace(-0.3, 0.3, 2000)
    flux = 1 + rng.normal(0, 1000e-6, ph.size)  # real scatter 1000 ppm
    np.savez(tmp_path / "lc.npz", phase_days=ph, flux=flux, flux_err=np.full(ph.size, 100e-6))
    cfg = {
        "tic_id": 1,
        "sectors": [5, 6],
        "apertures": {"5": [[1, 2]], "6": [[1, 2]]},
        "depth": 1e-3,
        "period_days": 3.0,
        "duration_days": 0.1,
        "lc_npz": str(tmp_path / "lc.npz"),
        "repeats": 3,
        "exptime_days": 1800 / 86400,
        "dilution_corrected": False,
    }
    return cfg | over


STARS_OK = pd.DataFrame({"mass": [1.0], "rad": [1.0], "Teff": [5800.0], "plx": [10.0]})


def test_run_fpp_noise_repeats_and_inputs(tmp_path):
    mod = _run_fpp_module()
    tgt = _FakeTarget(2, STARS_OK, [(0.10, 0.01), (0.12, 0.02), (0.14, 0.03)])
    res = mod.compute(_fpp_cfg(tmp_path), lambda *a: tgt)
    assert res["ok"] and res["repeats"] == 3
    assert res["fpp"] == pytest.approx(0.12) and res["fpp_std"] == pytest.approx(0.02)
    assert res["nfpp"] == pytest.approx(0.02)
    # flux_err_0 is the measured scatter (1000 ppm), not the pipeline error (100 ppm).
    assert res["flux_err_0"] == pytest.approx(1000e-6, rel=0.1)
    call = tgt.probs_calls[0]
    assert call["exptime"] == pytest.approx(1800 / 86400) and call["dilution_corrected"] is False
    assert tgt.depth_kw["dilution_corrected"] is False and len(tgt.depth_kw["all_ap_pixels"]) == 2


def test_run_fpp_refuses_bad_inputs(tmp_path):
    mod = _run_fpp_module()
    cfg = _fpp_cfg(tmp_path)
    degenerate = _FakeTarget(2, STARS_OK, [(1.0, 0.0)] * 3, degenerate=True)
    res = mod.compute(cfg, lambda *a: degenerate)
    assert not res["ok"] and "degenerate" in res["error"]
    no_plx = STARS_OK.assign(plx=[np.nan])
    res = mod.compute(cfg, lambda *a: _FakeTarget(2, no_plx, [(0.1, 0.0)] * 3))
    assert not res["ok"] and "plx" in res["error"]
    # triceratops dropped one sector: apertures would be paired with the wrong sectors.
    res = mod.compute(cfg, lambda *a: _FakeTarget(1, STARS_OK, [(0.1, 0.0)] * 3))
    assert not res["ok"] and "misaligned" in res["error"]
    # A sector without an aperture is not sent to triceratops at all.
    only5 = _fpp_cfg(tmp_path, apertures={"5": [[1, 2]]})
    tgt = _FakeTarget(1, STARS_OK, [(0.1, 0.0)] * 3)
    seen = {}
    res = mod.compute(only5, lambda tic, secs, cache: seen.setdefault("s", list(secs)) and tgt)
    assert res["ok"] and seen["s"] == [5]


def test_fpp_light_curve_uses_signal_windows_and_vetted_period(tmp_path, cfg, monkeypatch):
    """_fpp_for re-detrends like basic vetting: per-sector window >= 3 T14 and transits masked,
    folded at the vetted period (P/2 when halved). A stored 0.3 d window ate a 10 h transit."""
    from types import SimpleNamespace

    import planethunter.vetting.deep as deep
    from planethunter.ingest.lightcurves import fits_to_parquet
    from planethunter.pipeline import _fpp_for
    from tests.conftest import synthetic_sector, write_spoc_fits

    period, t0, dur, depth = 4.0, 1326.0, 10 / 24, 2000e-6
    df = synthetic_sector(planets=((period, t0, dur, depth),), noise=200e-6, seed=3)
    f = write_spoc_fits(tmp_path / "raw" / "7.fits", df, tic_id=7, sector=1)
    fits_to_parquet(f, tmp_path, delete_fits=True)
    seen = {}

    def fake_run_fpp(**kw):
        seen.update(kw)
        return {"ok": True, "fpp": 0.01, "nfpp": 0.0}

    monkeypatch.setattr(deep, "run_fpp", fake_run_fpp)
    r = SimpleNamespace(
        signal_id=1,
        tic_id=7,
        sectors="1",
        period_days=period,  # vetted period, already set by _deep_one
        t0_btjd=t0,
        detrend_window_days=0.3,
        detrend_windows_json='{"1": 0.3}',
        fit_depth_ppm=depth * 1e6,
    )
    res = _fpp_for(tmp_path, cfg, r, {1: [[0, 0]]}, dur)
    assert res["ok"] and seen["period_days"] == pytest.approx(period)
    ph, fl = seen["phase_days"], seen["flux"]
    base = np.median(fl[np.abs(ph) > dur])
    kept = (base - fl[np.abs(ph) < 0.3 * dur].mean()) / depth
    assert kept > 0.85, kept


def test_fpp_cadence_tolerates_measured_jitter():
    from planethunter.vetting.deep import fpp_test

    res = {"ok": True, "fpp": 0.01, "nfpp": 1e-5, "scenarios": []}
    for exp, ok in ((2.00015, True), (3.3333, False), (10.0, False)):
        tr = fpp_test(res, rp_rearth=3.0, snr=20.0, exptime_min=exp)
        assert tr.extra["cadence_ok"] is ok
