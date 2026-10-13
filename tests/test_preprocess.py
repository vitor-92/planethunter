import numpy as np
import pandas as pd
import pytest

from planethunter.preprocess import bin_lightcurve, flatten_sector, stitch
from tests.conftest import synthetic_sector


def _in_transit(t, period, t0, dur):
    phase = ((t - t0 + 0.5 * period) % period) - 0.5 * period
    return np.abs(phase) < dur / 2 * 0.6  # transit core


def test_detrending_removes_variability_but_keeps_transit_depth(cfg):
    P, T0, D, depth = 3.7, 1326.3, 3.0 / 24, 1500e-6
    df = synthetic_sector(planets=((P, T0, D, depth),), variability=0.003)
    lc = flatten_sector(df, 1, cfg.preprocess)
    full = _in_transit(lc.time, P, T0, D / 0.6)
    measured = 1 - np.mean(lc.flux[full])
    assert abs(measured - depth) / depth < 0.10
    out = lc.flux[~full]
    assert np.std(out) < 500e-6  # 3000 ppm variability removed down to ~noise


def test_upper_clip_removes_flares_not_dips(cfg):
    df = synthetic_sector(planets=((3.7, 1326.3, 3.0 / 24, 3000e-6),), variability=0.0)
    flare = (df["time"] > 1330.0) & (df["time"] < 1330.02)
    df.loc[flare, "flux"] *= 1.05
    lc = flatten_sector(df, 1, cfg.preprocess)
    assert lc.flux.max() < 1.003
    assert lc.flux.min() < 1 - 2500e-6  # transits survive


def test_quality_mask_drops_flagged_cadences(cfg):
    df = synthetic_sector()
    df.loc[100:199, "quality"] = 32  # momentum dump (Desat), in the default bitmask
    lc = flatten_sector(df, 1, cfg.preprocess)
    assert len(lc) <= len(df) - 100


def test_stitch_and_bin_preserve_order_and_sectors(cfg):
    a = flatten_sector(synthetic_sector(t_start=1325.0), 1, cfg.preprocess)
    b = flatten_sector(synthetic_sector(t_start=1353.0, seed=2), 2, cfg.preprocess)
    lc = stitch([b, a])
    assert np.all(np.diff(lc.time) > 0)
    assert lc.sectors == [1, 2]
    binned = bin_lightcurve(lc, 10)
    assert np.all(np.diff(binned.time) > 0)
    assert 4.0 < len(lc) / len(binned) < 5.5  # 2 min -> 10 min
    assert set(np.unique(binned.sector)) == {1, 2}


# ------------------------------------------------- audit 2026-10-10 (B2, transit mask, nulls)


def _depth(lc, P, T0, D):
    return 1 - float(np.mean(lc.flux[_in_transit(lc.time, P, T0, D)]))


def test_red_noise_ratio_ignores_deep_transits_but_flags_variability(cfg):
    """B2: a deep transit in white noise gives ~1 (np.std gave > 3); real variability > 1.2."""
    from planethunter.preprocess import flatten_adaptive, red_noise_ratio

    df = synthetic_sector(planets=((3.0, 1326.0, 5.0 / 24, 10000e-6),), variability=0.0)
    lc = flatten_sector(df, 1, cfg.preprocess)
    f = lc.flux.astype(float)
    old = np.std(f) / (np.std(np.diff(f)) / np.sqrt(2))
    assert old > 3.0  # the transit inflated the old ratio
    assert red_noise_ratio(f) < 1.1
    assert red_noise_ratio(f, lc.time, bin_hours=1.0) < 1.15  # Pont beta option
    assert flatten_adaptive(df, 1, cfg.preprocess).window_days == cfg.preprocess.window_length_days

    var = synthetic_sector(planets=(), variability=0.0, seed=3)
    t = var["time"].to_numpy()
    var["flux"] = (var["flux"] * (1 + 0.004 * np.sin(2 * np.pi * t / 0.9))).astype("f4")
    lc = flatten_sector(var, 1, cfg.preprocess)
    assert red_noise_ratio(lc.flux.astype(float)) > cfg.preprocess.red_noise_max
    assert red_noise_ratio(lc.flux.astype(float), lc.time, bin_hours=1.0) > 1.2


def test_windows_are_kept_per_sector_and_floored_at_3_t14(cfg):
    from planethunter.preprocess import signal_windows
    from planethunter.search.target import detrend_variants

    quiet = synthetic_sector(variability=0.0)
    var = synthetic_sector(variability=0.0, t_start=1353.0, seed=2)
    t = var["time"].to_numpy()
    var["flux"] = (var["flux"] * (1 + 0.004 * np.sin(2 * np.pi * t / 0.9))).astype("f4")
    variants = detrend_variants([(quiet, 1), (var, 2)], cfg)
    assert variants[0].windows == {1: 1.0, 2: 1.0}
    assert variants[1].windows[1] == 1.0 and variants[1].windows[2] < 1.0
    js = variants[1].windows_json()
    # Vetting: each sector its own window, never below 3 x T14 (T14 = 4 h -> 0.5 d).
    w = signal_windows(js, variants[1].window_days, 4.0 / 24, [1, 2], cfg.preprocess)
    assert w[1] == 1.0 and w[2] == pytest.approx(max(variants[1].windows[2], 0.5))
    # Missing JSON (old rows): fall back to detrend_window_days, then to the default.
    assert signal_windows(None, 0.3, 1.0 / 24, [1], cfg.preprocess) == {1: 0.3}
    assert signal_windows(None, None, 1.0 / 24, [1], cfg.preprocess) == {1: 1.0}


def test_masked_redetrend_keeps_a_12h_transit(cfg):
    """Rule: detrending must never eat the transit (12 h injection). A 1.0 d window keeps ~50 %
    of a 12 h transit; with the window floored at 3 x T14 and the transit masked, ~100 %
    (86 % with 2000 ppm / 5 d variability, against 42 % without the mask)."""
    from planethunter.preprocess import flatten_for_signal, signal_windows

    P, T0, D, depth = 10.0, 1327.0, 12.0 / 24, 2000e-6
    w = signal_windows('{"1": 0.5}', 0.5, D, [1], cfg.preprocess)
    assert w == {1: pytest.approx(1.5)}
    for var, keep in ((0.0, 0.9), (0.002, 0.8)):
        df = synthetic_sector(planets=((P, T0, D, depth),), variability=var, seed=4)
        plain = flatten_sector(df, 1, cfg.preprocess)
        assert _depth(plain, P, T0, D / 0.6) < 0.6 * depth
        lc = flatten_for_signal(
            [(df, 1)], cfg.preprocess, windows=w, period_days=P, t0_btjd=T0, duration_days=D
        )
        assert _depth(lc, P, T0, D / 0.6) > keep * depth


def test_flux_err_is_divided_by_the_trend(cfg):
    df = synthetic_sector(planets=(), variability=0.0, noise=100e-6)
    t = df["time"].to_numpy()
    trend = 1 + 0.2 * np.sin(2 * np.pi * t / 6.0)
    df["flux"] = (df["flux"] * trend).astype("f4")
    lc = flatten_sector(df, 1, cfg.preprocess)
    scaled = lc.flux_err * np.interp(lc.time, t, trend)  # constant if err was divided by trend
    assert np.std(scaled) / np.mean(scaled) < 0.01
    assert np.std(lc.flux_err) / np.mean(lc.flux_err) > 0.1


def test_null_inverted_turns_transits_into_bumps():
    from planethunter.preprocess import apply_null

    df = synthetic_sector(planets=((3.7, 1326.3, 3.0 / 24, 3000e-6),), variability=0.0)
    ((inv, s),) = apply_null([(df, 1)], "inverted", tic_id=1, seed=0, gap_days=0.5, cut_days=0.55)
    f, g = df["flux"].to_numpy(float), inv["flux"].to_numpy(float)
    assert s == 1 and np.allclose(f + g, 2 * np.median(f), rtol=1e-6)
    intr = _in_transit(df["time"].to_numpy(), 3.7, 1326.3, 3.0 / 24 / 0.6)
    assert np.median(g[intr]) / np.median(g) - 1 == pytest.approx(3000e-6, rel=0.1)


def test_null_scrambled_breaks_periodicity_across_segments():
    from planethunter.preprocess import apply_null

    P, T0, D = 3.7, 1326.3, 3.0 / 24
    df = synthetic_sector(planets=((P, T0, D, 3000e-6),), variability=0.0, noise=100e-6)
    df["quality"] = np.arange(len(df)) % 7  # tracer: must travel with the flux
    kw = dict(tic_id=42, seed=0, gap_days=0.5, cut_days=0.55)
    ((sc, _),) = apply_null([(df, 1)], "scrambled", **kw)
    ((again, _),) = apply_null([(df, 1)], "scrambled", **kw)
    pd.testing.assert_frame_equal(sc, again)  # deterministic per (seed, tic, sector)
    assert len(df) - 2 * 0.55 * 720 - 10 < len(sc) < len(df)  # only the 2 junctions cut
    # Time stamps are kept; flux and quality moved together.
    orig = df.set_index("quality")["flux"].groupby(level=0).mean()
    new = sc.set_index("quality")["flux"].groupby(level=0).mean()
    assert np.all(np.isin(sc["time"].to_numpy(), df["time"].to_numpy()))
    assert np.allclose(orig, new, rtol=1e-3)
    # The folded transit at the true ephemeris loses most of its depth.
    t, f = sc["time"].to_numpy(), sc["flux"].to_numpy(float)
    intr = _in_transit(t, P, T0, D)
    folded = 1 - np.mean(f[intr]) / np.median(f)
    assert folded < 0.6 * 3000e-6
    with pytest.raises(ValueError):
        apply_null([(df, 1)], "reversed", **kw)


def test_masked_redetrend_protects_phase_half_for_period_halving(cfg):
    """A signal found at 2P: the transits in between (phase 0.5) are masked too, so the
    `period_halved` vetting test sees their full depth."""
    from planethunter.preprocess import flatten_for_signal

    P, T0, D, depth = 6.0, 1327.0, 10.0 / 24, 2000e-6
    df = synthetic_sector(planets=((P, T0, D, depth),), variability=0.0, seed=6)
    kw = dict(windows={1: 1.0}, period_days=2 * P, t0_btjd=T0, duration_days=D)
    half = flatten_for_signal([(df, 1)], cfg.preprocess, **kw)
    only = flatten_for_signal([(df, 1)], cfg.preprocess, mask_half_phase=False, **kw)
    mid = (2 * P, T0 + P, D / 0.6)  # the in-between transits
    assert _depth(half, *mid) > 0.9 * depth
    assert _depth(only, *mid) < 0.8 * depth
