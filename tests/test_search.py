import json

import numpy as np
import pytest

from planethunter.models import StarParams
from planethunter.preprocess import flatten_sector
from planethunter.search import search_periodic
from planethunter.search.tls import edge_fraction, segment_edges
from tests.conftest import synthetic_sector

SUN = StarParams(tic_id=1, radius_rsun=1.0, mass_msun=1.0)


def test_tls_recovers_injected_planet(cfg):
    lc = flatten_sector(
        synthetic_sector(planets=((3.7, 1326.3, 2.5 / 24, 1500e-6),)), 1, cfg.preprocess
    )
    sigs = search_periodic(lc, SUN, cfg.search, tic_id=1)
    assert sigs, "no signals"
    s = sigs[0]
    assert s.period_days == pytest.approx(3.7, rel=0.01)
    assert s.depth_ppm == pytest.approx(1500, rel=0.25)
    assert s.sde >= cfg.vetting.sde_min
    assert s.n_transits >= 6
    assert s.sectors == "1" and s.author == "SPOC"


def test_iterative_search_finds_second_planet(cfg):
    planets = ((3.7, 1326.3, 2.5 / 24, 2000e-6), (6.9, 1327.1, 3.0 / 24, 1200e-6))
    lc = flatten_sector(synthetic_sector(planets=planets, noise=300e-6), 1, cfg.preprocess)
    sigs = search_periodic(lc, SUN, cfg.search, tic_id=1)
    periods = sorted(s.period_days for s in sigs if s.sde >= cfg.vetting.sde_min)
    assert any(abs(p - 3.7) / 3.7 < 0.01 for p in periods)
    assert any(abs(p - 6.9) / 6.9 < 0.01 for p in periods)


def _passes_detection_gate(s, cfg):
    v = cfg.vetting
    return (
        s.sde >= v.sde_min
        and s.snr >= v.snr_min
        and s.n_transits >= v.min_transits
        and s.edge_transit_fraction <= v.max_edge_transit_fraction
    )


QLP_SNR_PINK_MIN = 9.0  # Kunimoto et al. 2023: S/N_pink > 9 (not gated in production yet)


@pytest.mark.parametrize("seed", [7, 8, 9])
def test_pure_noise_with_variability_yields_no_candidate(cfg, seed):
    """Noise + 2000 ppm variability (5 d sinusoid).

    Edge ramps reach SDE ~11 and are stopped by the edge-fraction cut. The residual of the
    sinusoid after the 1.0 d biweight is a real periodic dip (P ~ 5 d, T14 ~ 13 h) whose SDE sits
    at 7.8-9.8 depending on the grid (old grid: 7.8; old grid + TESS LD or n_transits_min = 2
    alone: 9.1-9.4), so SDE/SNR alone cannot be relied on. S/N_pink (Pont 2006, on T14) stays
    below the QLP threshold for every noise signal that passes the SQL gate.
    """
    lc = flatten_sector(synthetic_sector(planets=(), seed=seed), 1, cfg.preprocess)
    sigs = search_periodic(lc, SUN, cfg.search, tic_id=1)
    passing = [s for s in sigs if _passes_detection_gate(s, cfg)]
    assert all(s.extra["snr_pink"] < QLP_SNR_PINK_MIN for s in passing)


def test_edge_fraction_flags_transits_at_segment_edges():
    t = np.r_[np.arange(0.0, 13.0, 0.01), np.arange(14.0, 27.0, 0.01)]
    edges = np.round(segment_edges(t, gap_days=0.5), 6)
    assert list(edges) == [0.0, 12.99, 14.0, 26.99]
    assert edge_fraction(np.array([0.07, 6.5]), edges, 0.5) == 0.5
    assert edge_fraction(np.array([3.0, 9.0, 20.0]), edges, 0.5) == 0.0


def test_real_planet_passes_detection_gate(cfg):
    lc = flatten_sector(synthetic_sector(), 1, cfg.preprocess)
    sigs = search_periodic(lc, SUN, cfg.search, tic_id=1)
    assert _passes_detection_gate(sigs[0], cfg)
    assert sigs[0].extra["snr_pink"] >= QLP_SNR_PINK_MIN


def test_missing_stellar_params_falls_back(cfg):
    lc = flatten_sector(synthetic_sector(), 1, cfg.preprocess)
    sigs = search_periodic(lc, StarParams(tic_id=1), cfg.search, tic_id=1)
    assert sigs and sigs[0].period_days == pytest.approx(3.7, rel=0.01)


def test_adaptive_window_recovers_planet_on_fast_rotator(cfg):
    """Regression TOI 862.01: fast variability requires a window shorter than 1.0 d."""
    import numpy as np

    from planethunter.preprocess import flatten_adaptive, red_noise_ratio

    df = synthetic_sector(planets=((3.3, 1326.0, 2.5 / 24, 3000e-6),), variability=0.0, seed=3)
    t = df["time"].to_numpy()
    df["flux"] = (df["flux"] * (1 + 0.004 * np.sin(2 * np.pi * t / 0.9))).astype("f4")
    fixed = flatten_sector(df, 1, cfg.preprocess)
    adaptive = flatten_adaptive(df, 1, cfg.preprocess)
    assert red_noise_ratio(fixed.flux.astype(float)) > cfg.preprocess.red_noise_max
    assert adaptive.window_days < cfg.preprocess.window_length_days
    sigs = search_periodic(adaptive, SUN, cfg.search, tic_id=1)
    assert sigs and abs(sigs[0].period_days - 3.3) / 3.3 < 0.01
    assert sigs[0].detrend_window_days == adaptive.window_days


def test_short_transit_on_subgiant_is_in_duration_grid(cfg):
    """Regression TOI 196.01/347.01: a 1 h transit (high b) on an R=2.5 star must not vanish."""
    df = synthetic_sector(planets=((4.04, 1326.0, 1.0 / 24, 1500e-6),), noise=500e-6, seed=4)
    lc = flatten_sector(df, 1, cfg.preprocess)
    star = StarParams(tic_id=1, radius_rsun=2.5, mass_msun=1.3)
    sigs = search_periodic(lc, star, cfg.search, tic_id=1)
    assert any(abs(s.period_days - 4.04) / 4.04 < 0.01 and s.sde >= 9 for s in sigs)


def test_variants_keep_long_transit_on_red_noise_star(cfg):
    """Regression TOI 190.01: a short window eats a 5.7 h transit; the default variant keeps it."""
    import numpy as np

    from planethunter.search import search_target
    from planethunter.search.target import detrend_variants

    df = synthetic_sector(planets=((10.02, 1328.0, 5.7 / 24, 6000e-6),), variability=0.0, seed=5)
    t = df["time"].to_numpy()
    df["flux"] = (df["flux"] * (1 + 0.0006 * np.sin(2 * np.pi * t / 1.3))).astype("f4")
    variants = detrend_variants([(df, 1)], cfg)
    assert len(variants) == 2 and variants[1].window_days < 1.0  # red noise triggered the variant
    sigs = search_target([(df, 1)], SUN, cfg, tic_id=1)
    assert any(abs(s.period_days - 10.02) / 10.02 < 0.01 for s in sigs)
    assert len({round(s.period_days, 2) for s in sigs}) == len(sigs)  # no duplicates


def test_template_star_is_capped_so_short_periods_stay_in_grid(cfg):
    """Regression TOI 196.01: R_TIC = 4 must not cut P = 1.16 d from the grid."""
    df = synthetic_sector(planets=((1.163, 1325.5, 1.4 / 24, 800e-6),), noise=400e-6, seed=6)
    lc = flatten_sector(df, 1, cfg.preprocess)
    giant = StarParams(tic_id=1, radius_rsun=4.06, mass_msun=1.4)
    sigs = search_periodic(lc, giant, cfg.search, tic_id=1)
    assert any(abs(s.period_days - 1.163) / 1.163 < 0.01 for s in sigs)


def test_refine_alias_recovers_true_period_from_p_over_3():
    """Regression TOI 899.01: 2 real transits, TLS returns P/3; extra epochs have no transit."""
    import numpy as np

    from planethunter.search.tls import refine_alias

    rng = np.random.default_rng(0)
    t = np.arange(1325.0, 1350.0, 10 / 1440)
    f = 1 + rng.normal(0, 1000e-6, t.size)
    true_p, t0, dur = 12.85, 1330.0, 3.0 / 24
    for ep in (t0, t0 + true_p):
        f[np.abs(t - ep) < dur / 2] -= 8000e-6
    ref = refine_alias(t, f, true_p / 3, t0, dur)
    assert ref is not None and ref.factor == 3
    assert abs(ref.period_days - true_p) < 1e-6 and abs(ref.t0_btjd - t0) < 1e-6
    assert ref.depth_ppm == pytest.approx(8000, rel=0.15)
    # The true period must not be "refined".
    assert refine_alias(t, f, true_p, t0, dur) is None


# ------------------------------------------------- audit 2026-10-10 (A5, A6, B1, B10, B11)


def _two_sectors_700d(planet, noise=400e-6):
    return [
        (synthetic_sector(planets=(planet,), variability=0.0, noise=noise, seed=11), 1),
        (
            synthetic_sector(
                planets=(planet,), variability=0.0, noise=noise, seed=12, t_start=2025.0
            ),
            2,
        ),
    ]


def test_tls_duration_is_physical_on_gapped_multisector(cfg):
    """A5: TLS reports T14 x fill factor (0.07 here, 3 h -> 0.2 h). duration_hours must be T14,
    the SNR must not collapse and the iterative mask must not return the same period again."""
    from planethunter.preprocess import stitch
    from planethunter.search.stats import white_snr

    P, T0, D, depth = 6.27, 1326.3, 3.0 / 24, 1500e-6
    frames = _two_sectors_700d((P, T0, D, depth))
    lc = stitch([flatten_sector(df, s, cfg.preprocess) for df, s in frames])
    sigs = search_periodic(lc, SUN, cfg.search, tic_id=1)
    s = sigs[0]
    assert s.period_days == pytest.approx(P, rel=1e-3)
    assert s.extra["duration_raw_hours"] < 0.5  # the TLS value is shrunk by the fill factor
    assert s.duration_hours == pytest.approx(3.0, rel=0.25)
    truth = white_snr(lc.time, lc.flux.astype(float), P, T0, D).snr
    assert s.snr > 0.8 * truth
    assert s.snr > 2.0 * s.extra["snr_tls"]  # the TLS SNR used the shrunken window
    assert len([x for x in sigs if abs(x.period_days / P - 1) < 0.01]) == 1
    # B11: epochs counted with the corrected T14 (2 sectors x ~4 transits, minus gaps).
    assert s.n_transits == len(json.loads(s.transit_times_json)) >= 6


def test_observed_epochs_require_half_of_t14_covered():
    """B11: an epoch counts only if >= 50 % of [-T14/2, +T14/2] has data."""
    from planethunter.search.stats import observed_epochs

    P, t0, t14 = 5.0, 100.0, 0.2
    t = np.arange(97.0, 116.0, 2 / 1440)
    # epoch 105: only the first 30 % of the window has data; epoch 110: 60 %; 100, 115: full.
    cut_a = (t > 105 - 0.1 + 0.3 * t14) & (t < 105.5)
    cut_b = (t > 110 - 0.1 + 0.6 * t14) & (t < 110.5)
    t = t[~(cut_a | cut_b)]
    got = observed_epochs(t, P, t0, t14, min_coverage=0.5)
    assert list(np.round(got, 6)) == [100.0, 110.0, 115.0]


def _alias_case(k: int):
    rng = np.random.default_rng(k)
    t = np.arange(1325.0, 1352.0, 10 / 1440)
    f = 1 + rng.normal(0, 1000e-6, t.size)
    true_p, t0, dur = (12.85, 1330.0, 3.0 / 24) if k == 3 else (9.1, 1328.0, 3.0 / 24)
    for ep in np.arange(t0, t[-1], true_p):
        f[np.abs(t - ep) < dur / 2] -= 6000e-6
    return t, f, true_p, t0, dur


@pytest.mark.parametrize("k", [2, 3])
def test_refine_alias_returns_snr_of_the_true_period(k):
    """A6: the SNR after refine_alias is measured on the k*P epochs only (was sqrt(n_A/n) low)."""
    from planethunter.search.stats import white_snr
    from planethunter.search.tls import refine_alias

    t, f, true_p, t0, dur = _alias_case(k)
    ref = refine_alias(t, f, true_p / k, t0, dur)
    assert ref is not None and ref.factor == k
    at_truth = white_snr(t, f, true_p, t0, dur).snr
    at_alias = white_snr(t, f, true_p / k, t0, dur).snr
    assert ref.snr == pytest.approx(at_truth, rel=1e-6)
    assert ref.snr > 0.9 * np.sqrt(k) * at_alias  # sqrt(n / n_A) = sqrt(k) with no gaps


def test_rp_rs_follows_depth():
    from planethunter.search.tls import _rp_rs

    small, big = _rp_rs(1000e-6, (0.4, 0.2)), _rp_rs(4000e-6, (0.4, 0.2))
    assert 0.025 < small < 0.04 and big == pytest.approx(2 * small, rel=0.05)


def test_period_grid_reaches_short_periods_and_most_of_the_span(cfg):
    """B1: P_min from a = 2 R* (QLP) and P_max = 0.9 x span (TLS n_transits_min = 1)."""
    import warnings

    from transitleastsquares.grid import period_grid

    from planethunter.search.tls import _grid_kwargs

    g = _grid_kwargs(SUN, cfg.search)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        new = period_grid(
            g["R_star"],
            g["M_star"],
            27.0,
            oversampling_factor=g["oversampling_factor"],
            n_transits_min=cfg.search.n_transits_min,
        )
        old = period_grid(1.0, 1.0, 27.0, oversampling_factor=3, n_transits_min=2)
    assert new.min() == pytest.approx(0.33, abs=0.02)  # a = 2 R_sun
    assert old.min() == pytest.approx(0.60, abs=0.02)  # a = 3 R_sun
    assert new.max() > 26.0 and old.max() < 13.6
    # Same Ofir density in the overlap (R* and the oversampling scaled together).
    n_new = np.sum((new > 1) & (new < 10))
    n_old = np.sum((old > 1) & (old < 10))
    assert n_new == pytest.approx(n_old, rel=0.02)


def test_ultra_short_and_long_periods_are_found(cfg):
    """B1: P = 0.45 d (below the old 0.6 d floor) and P = 16 d (above the old span/2)."""
    usp = synthetic_sector(planets=((0.45, 1325.2, 1.0 / 24, 1500e-6),), variability=0.0)
    sigs = search_periodic(flatten_sector(usp, 1, cfg.preprocess), SUN, cfg.search, tic_id=1)
    assert any(abs(s.period_days - 0.45) / 0.45 < 0.005 for s in sigs)
    lp = synthetic_sector(planets=((16.0, 1330.0, 4.0 / 24, 2000e-6),), variability=0.0)
    sigs = search_periodic(flatten_sector(lp, 1, cfg.preprocess), SUN, cfg.search, tic_id=1)
    assert any(abs(s.period_days - 16.0) / 16.0 < 0.01 and s.n_transits == 2 for s in sigs)


def test_snr_pink_matches_white_snr_in_white_noise_and_drops_with_red_noise():
    """B10: S/N_pink (Pont 2006) ~ white SNR for white noise, lower with T14-scale red noise."""
    from planethunter.search.stats import pink_snr, white_snr

    rng = np.random.default_rng(5)
    t = np.arange(0.0, 27.0, 10 / 1440)
    P, t0, dur = 3.3, 1.0, 3.0 / 24
    white = 1 + rng.normal(0, 500e-6, t.size)
    phase = np.abs((t - t0 + P / 2) % P - P / 2)
    white[phase < dur / 2] -= 1000e-6
    w, pk = white_snr(t, white, P, t0, dur).snr, pink_snr(t, white, P, t0, dur)
    assert pk == pytest.approx(w, rel=0.25)
    walk = np.convolve(rng.normal(0, 1, t.size), np.ones(36) / 36, mode="same")  # ~6 h
    red = white + 300e-6 * walk / np.std(walk)
    assert pink_snr(t, red, P, t0, dur) < 0.7 * white_snr(t, red, P, t0, dur).snr


def test_signal_row_has_new_db_columns(cfg):
    from planethunter.search import signal_row

    lc = flatten_sector(synthetic_sector(), 1, cfg.preprocess)
    row = signal_row(search_periodic(lc, SUN, cfg.search, tic_id=1)[0])
    assert row["duration_raw_hours"] > 0 and row["snr_pink"] > 0
    assert json.loads(row["detrend_windows_json"]) == {"1": 1.0}


def test_tess_limb_darkening_from_local_table(cfg):
    from planethunter.search.tls import limb_darkening

    u_sun = limb_darkening(StarParams(tic_id=1, teff_k=5750, logg_cgs=4.5), cfg.search)
    u_m = limb_darkening(StarParams(tic_id=1, teff_k=3300, logg_cgs=5.0), cfg.search)
    assert u_sun != u_m and all(0 < x < 1 for x in u_sun)
    assert limb_darkening(StarParams(tic_id=1), cfg.search) == (0.4804, 0.1867)


def test_gpu_bls_grid_is_ofir_and_bins_resolve_short_durations(cfg):
    from planethunter.search.gpu_bls import DURATIONS_H, n_phase_bins, period_grid

    p = period_grid(27.0, cfg.search)
    assert p.min() == pytest.approx(cfg.search.period_min_days, rel=1e-3)
    assert p.max() == pytest.approx(0.9 * 27.0, rel=1e-3)
    q = np.sort(1 / p) ** (1 / 3)
    assert np.allclose(np.diff(q), np.diff(q)[0], rtol=1e-6)  # uniform in f^(1/3)
    for P in (0.3, 5.0, 24.0):
        assert P / n_phase_bins(P) <= min(DURATIONS_H) / 24 / 2 + 1e-12


def test_vetting_a_null_run_signal_uses_transformed_flux(tmp_path, cfg, monkeypatch):
    """Signals of a null run are vetted on the same transformed light curve the search saw."""
    import planethunter.vetting as vetting
    from planethunter.ingest.lightcurves import fits_to_parquet, read_parquet
    from planethunter.pipeline import _vet_target
    from tests.conftest import write_spoc_fits

    df = synthetic_sector(planets=((3.7, 1326.3, 3.0 / 24, 3000e-6),), variability=0.0)
    path, _ = fits_to_parquet(
        write_spoc_fits(tmp_path / "raw" / "5.fits", df, tic_id=5, sector=1),
        tmp_path,
        delete_fits=True,
    )
    original, _ = read_parquet(path)
    seen = {}

    def fake_vet(sig, flat, raw, *args, **kwargs):
        seen["flat"], seen["raw"] = flat, raw
        raise RuntimeError("captured")

    monkeypatch.setattr(vetting, "vet_signal", fake_vet)
    row = dict(
        signal_id=1,
        period_days=3.7,
        t0_btjd=1326.3,
        duration_hours=3.0,
        depth_ppm=3000.0,
        sde=20.0,
        snr=30.0,
        n_transits=6,
        edge_transit_fraction=0.0,
        detrend_window_days=1.0,
        detrend_windows_json='{"1": 1.0}',
        _gated=True,
    )
    cfg_json = cfg.model_dump_json()
    for mode in (None, "inverted"):
        res = _vet_target(5, [str(path)], [row], cfg_json, mode)
        assert "captured" in res["error"]
        flat = seen["flat"]
        ph = np.abs((flat.time - 1326.3 + 1.85) % 3.7 - 1.85)
        dip = 1 - float(np.mean(flat.flux[ph < 1.0 / 24]))
        if mode is None:
            assert dip == pytest.approx(3000e-6, rel=0.2)
        else:
            # Inverted: the transit is a bump, removed by the upper clip (no points, or no dip).
            assert np.isnan(dip) or dip < 500e-6
            med = float(np.nanmedian(original["flux"]))
            raw = seen["raw"].sort_values("time")["flux"].to_numpy(np.float64)
            want = 2 * med - original.sort_values("time")["flux"].to_numpy(np.float64)
            assert np.allclose(raw, want, rtol=1e-5)
