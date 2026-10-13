"""Basic vetting on synthetic curves: each test must catch the false positive it targets."""

import numpy as np
import pandas as pd
import pytest

from planethunter.config import VettingConfig
from planethunter.models import StarParams
from planethunter.preprocess.clean import FlatLightCurve
from planethunter.vetting import VetSignal, vet_signal
from planethunter.vetting.basic import predicted_duration_days, trapezoid

SUN = StarParams(tic_id=1, radius_rsun=1.0, mass_msun=1.0)
CFG = VettingConfig()
P, T0 = 3.7, 1326.3


def make(
    depth=2000e-6,
    dur_h=2.8,
    odd_depth=None,
    secondary=0.0,
    tau_frac=0.1,
    noise=300e-6,
    single_extra=None,
    centroid_shift=0.0,
    seed=0,
    sec_phase=0.5,
):
    rng = np.random.default_rng(seed)
    t = np.arange(1325.0, 1352.0, 2 / 1440)
    t = t[(t < 1338.0) | (t > 1339.0)]
    dur = dur_h / 24
    n = np.round((t - T0) / P).astype(int)
    ph = t - (T0 + n * P)
    depths = np.where((n % 2 == 1) & (odd_depth is not None), odd_depth or 0, depth)
    model = np.ones_like(t)
    for e in np.unique(n):
        m = n == e
        model[m] = trapezoid(ph[m], depths[m][0], dur, tau_frac * dur, 0.0)
    if secondary:
        ph2 = ((t - T0) % P) - sec_phase * P
        model[np.abs(ph2) < dur / 2] -= secondary
    if single_extra:
        model[(n == 2) & (np.abs(ph) < dur / 2)] -= single_extra
    f = model + rng.normal(0, noise, t.size)
    lc = FlatLightCurve(t, f.astype("f4"), np.full(t.size, noise, "f4"), np.ones(t.size, "i2"), 1.0)
    intr = (1 - model) > 0
    raw = pd.DataFrame(
        {
            "time": t,
            "quality": np.zeros(t.size, "i4"),
            "mom_centr1": 1000 + rng.normal(0, 0.002, t.size) + centroid_shift * intr,
            "mom_centr2": 500 + rng.normal(0, 0.002, t.size),
        }
    )
    sig = VetSignal(P, T0, dur, depth * 1e6, sde=20, snr=30, n_transits=7)
    return sig, lc, raw


def test_clean_planet_passes_all_basic_tests():
    rep = vet_signal(*make(), SUN, CFG)
    assert rep.verdict == "PASS_BASIC", [(t.name, t.passed, t.note) for t in rep.tests]
    assert not rep.failed and not rep.vetoed_by
    assert rep.fit["depth_ppm"] == pytest.approx(2000, rel=0.15)


def test_odd_even_mismatch_vetoes_eb_at_half_period():
    rep = vet_signal(*make(depth=4000e-6, odd_depth=1000e-6), SUN, CFG)
    assert "odd_even" in rep.vetoed_by and rep.verdict == "FAIL"


def test_secondary_eclipse_vetoes():
    rep = vet_signal(*make(secondary=1500e-6), SUN, CFG)
    assert "secondary" in rep.vetoed_by
    # 1500 vs 2000 ppm is many sigma apart: a real secondary, not the in-between transit.
    assert all(t.name != "period_halved" for t in rep.tests)


def test_giant_radius_vetoes_only_with_reliable_star_and_eb_sign():
    """Mullally+2015: the radius alone is not a false-positive verdict."""
    # Rp ~ 38 R_earth, U-shaped: soft fail only (no other EB sign).
    rep = vet_signal(*make(depth=0.12), SUN, CFG)
    assert "radius" in rep.failed and "radius" not in rep.vetoed_by
    assert "veto withheld" in rep.test("radius").note
    # Same radius and V-shaped on a dwarf: veto.
    rep = vet_signal(*make(depth=0.12, tau_frac=0.5, noise=300e-6), SUN, CFG)
    assert "radius" in rep.vetoed_by
    # V-shaped but the star is evolved (log g 3.0): R* unreliable, no radius veto.
    evolved = StarParams(tic_id=1, radius_rsun=1.0, mass_msun=1.0, logg_cgs=3.0)
    rep = vet_signal(*make(depth=0.12, tau_frac=0.5, noise=300e-6), evolved, CFG)
    assert "radius" not in rep.vetoed_by and "radius" in rep.failed


def test_v_shape_fails():
    rep = vet_signal(*make(depth=5000e-6, tau_frac=0.5, noise=100e-6), SUN, CFG)
    assert "shape" in rep.failed


def test_too_long_duration_for_star_fails():
    # Sun, P = 3.7 d -> T14(b=0) ~ 3.0 h; 6 h requires a larger star (blend or wrong R*).
    assert predicted_duration_days(P, SUN) * 24 == pytest.approx(3.0, abs=0.3)
    rep = vet_signal(*make(dur_h=6.0), SUN, CFG)
    assert "duration" in rep.failed


def test_centroid_shift_fails():
    rep = vet_signal(*make(centroid_shift=0.01), SUN, CFG)
    assert "centroid" in rep.failed


def test_single_dominant_event_fails_consistency():
    sig, lc, raw = make(depth=300e-6, single_extra=5000e-6)
    rep = vet_signal(sig, lc, raw, SUN, CFG)
    assert "consistency" in rep.failed


def test_missing_star_marks_unknown_not_failed():
    rep = vet_signal(*make(), StarParams(tic_id=1), CFG)
    assert rep.test("radius").passed is None and rep.test("duration").passed is None
    assert rep.verdict == "PASS_BASIC"


def test_small_planetary_occultation_is_not_vetoed():
    """Regression, WASP-18 b: an occultation of ~3 % of the transit is planetary physics, not EB."""
    rep = vet_signal(*make(depth=10000e-6, secondary=300e-6, noise=150e-6), SUN, CFG)
    assert "secondary" not in rep.vetoed_by
    assert rep.test("secondary").passed is False  # flagged for review


def test_eccentric_secondary_found_by_phase_scan():
    """Regression, TOI-367.01 (eccentric EB): secondary away from phase 0.5."""
    rep = vet_signal(*make(secondary=1500e-6, sec_phase=0.32), SUN, CFG)
    assert "secondary_scan" in rep.failed
    assert "0.32" in rep.test("secondary_scan").note or "0.31" in rep.test("secondary_scan").note


def test_detection_gates_are_vetoes():
    sig, lc, raw = make()
    sig.snr = 5.0
    assert "snr" in vet_signal(sig, lc, raw, SUN, CFG).vetoed_by
    sig.snr, sig.n_transits = 30, 1
    assert "n_transits" in vet_signal(sig, lc, raw, SUN, CFG).vetoed_by


def test_severity_rules():
    from planethunter.alerts.severity import severity

    assert severity("NEW", "PASS_BASIC", 1.0) == "P1"  # no deep vetting: capped at P1
    assert severity("NEW", "PASS_BASIC", 0.6) == "P2"
    # P0 also needs the Giacalone+2021 validation region (NFPP, Rp, SNR, 2-min cadence).
    region = dict(nfpp=1e-4, rp_rearth=2.0, snr=20.0, two_min_cadence=True)
    assert severity("NEW", "PASS_BASIC", 0.9, deep_done=True, fpp=0.05, **region) == "P0"
    assert severity("NEW", "PASS_BASIC", 0.9, deep_done=True, fpp=0.05) == "P1"  # unverifiable
    assert severity("NEW", "PASS_BASIC", 0.9, deep_done=True, fpp=0.3, **region) == "P1"
    assert severity("NEW", "FAIL", 1.0) == "NONE"
    assert severity("KNOWN_TOI", "PASS_BASIC", 1.0) == "NONE"
    assert severity("UNVERIFIED", "PASS_BASIC", 1.0) == "NONE"


def test_duplicate_signal_is_vetoed_by_independence():
    """Regression, signal 1601: masking the stronger signal removes all of this one's transits."""
    sig, lc, raw = make()
    rep = vet_signal(sig, lc, raw, SUN, CFG, other_signals=[(P, T0, sig.duration_days)])
    assert "independence" in rep.vetoed_by


def test_too_short_duration_for_giant_fails():
    """Regression, signal 1594: 0.58 h on an R = 3 giant (predicted ~10 h)."""
    giant = StarParams(tic_id=1, radius_rsun=3.06, mass_msun=1.3)
    rep = vet_signal(*make(dur_h=0.6, depth=1000e-6, noise=150e-6), giant, CFG)
    assert "duration" in rep.failed


def test_eb_host_caps_severity():
    from planethunter.alerts.severity import severity

    assert severity("NEW", "PASS_BASIC", 1.0, host_eb=True) == "P2"


# ---------------------------------------------------------------- audit 2026-10-10


def _names(rep):
    return [t.name for t in rep.tests]


def test_planet_found_at_twice_the_period_is_halved():
    """A7, TOI-431 b: at 2P the in-between transit looks like a 'secondary' and was vetoed."""
    sig, lc, raw = make()
    sig2 = VetSignal(2 * P, T0, sig.duration_days, sig.depth_ppm, sde=20, snr=21, n_transits=4)
    rep = vet_signal(sig2, lc, raw, SUN, CFG)
    assert "period_halved" in _names(rep), [(t.name, t.passed, t.note) for t in rep.tests]
    assert rep.period_days == pytest.approx(P)
    assert rep.test("period_halved").value == pytest.approx(P)
    assert rep.verdict == "PASS_BASIC" and not rep.vetoed_by
    assert rep.test("snr").value > 21  # both sets of transits count at P/2
    assert rep.test("n_transits").value >= 6


def test_twin_eb_at_twice_the_period_fails_after_halving():
    """Equal eclipses at 2P are halved too; at P/2 the V shape and the radius catch the EB."""
    _, lc, raw = make(depth=0.12, tau_frac=0.5, noise=300e-6)
    sig2 = VetSignal(2 * P, T0, 2.8 / 24, 120000, sde=40, snr=200, n_transits=4)
    rep = vet_signal(sig2, lc, raw, SUN, CFG)
    assert "period_halved" in _names(rep)
    assert rep.verdict == "FAIL"
    assert "shape" in rep.failed and "radius" in rep.vetoed_by


def test_clean_planet_is_not_halved():
    rep = vet_signal(*make(), SUN, CFG)
    assert "period_halved" not in _names(rep) and rep.period_days == pytest.approx(P)


def test_verdict_counts_soft_fails_and_hard_fails():
    """B6: one soft fail keeps PASS_BASIC (ranked lower); two soft fails or a hard fail = FAIL."""
    from planethunter.vetting.basic import TestResult, _score

    ok = [TestResult("sde", 20, 9, True), TestResult("snr", 30, 7.1, True)]
    one = _score([*ok, TestResult("duration", 2.0, 1.67, False)], CFG, None)
    assert one.verdict == "PASS_BASIC" and one.score == pytest.approx(CFG.weights["duration"])
    two = _score(
        [*ok, TestResult("duration", 2.0, 1.67, False), TestResult("shape", 0.5, 0.35, False)],
        CFG,
        None,
    )
    assert two.verdict == "FAIL" and two.failed == ["duration", "shape"]
    hard = _score([*ok, TestResult("tpf_difference_image", 3.0, 1.0, False)], CFG, None)
    assert hard.verdict == "FAIL"
    veto = _score([*ok, TestResult("odd_even", 9.0, 3.0, False, veto=True)], CFG, None)
    assert veto.verdict == "FAIL" and veto.score == 0.0


def test_duration_ceiling_is_1_67():
    """LEO-Vetter / Kipping 2010: 1.5x the b=0 duration is allowed (eccentric orbits)."""
    assert CFG.duration_ratio_max == pytest.approx(1.67)
    rep = vet_signal(*make(dur_h=4.5, noise=200e-6), SUN, CFG)  # ratio ~1.5
    assert rep.test("duration").passed is True, rep.test("duration").note


def test_trapezoid_on_its_bound_is_unconstrained():
    """A fit whose T14 sits on its bound is not a duration measurement (467 NEW in s107)."""
    from planethunter.vetting.basic import fit_trapezoid

    sig, lc, raw = make(dur_h=8.0, depth=3000e-6, noise=200e-6)
    ph = ((lc.time - T0 + 0.5 * P) % P) - 0.5 * P
    fit = fit_trapezoid(ph, lc.flux.astype(float), 3000e-6, (8.0 / 24) / 10)
    assert fit is not None and fit["t14_at_bound"]
    sig.duration_days = (8.0 / 24) / 10  # search duration far too short
    rep = vet_signal(sig, lc, raw, SUN, CFG)
    dur = rep.test("duration")
    assert dur.passed is None and dur.value is None and "bound" in dur.note
    assert rep.fit["t14_at_bound"] is True
    # A modest underestimate (x 1/4) is recovered by the wider second fit.
    fit = fit_trapezoid(ph, lc.flux.astype(float), 3000e-6, (8.0 / 24) / 4)
    assert not fit["t14_at_bound"] and fit["t14_days"] * 24 == pytest.approx(8.0, rel=0.15)


def _centroid_raw(shift_by_sector, red=0.0, seed=0, n_days=27.0):
    """Centroids only. shift_by_sector: {sector: shift_px}; sectors are consecutive blocks."""
    rng = np.random.default_rng(seed)
    frames = []
    for i, (sec, shift) in enumerate(shift_by_sector.items()):
        t = np.arange(1325.0 + i * n_days, 1325.0 + (i + 1) * n_days, 2 / 1440)
        n = np.round((t - T0) / P)
        intr = np.abs(t - (T0 + n * P)) < 1.4 / 24
        c1 = 1000 + rng.normal(0, 0.002, t.size) + shift * intr
        if red:
            kern = np.exp(-0.5 * (np.arange(-150, 151) / 50.0) ** 2)
            w = np.convolve(rng.normal(0, 1, t.size), kern / np.sqrt((kern**2).sum()), "same")
            c1 = c1 + red * w
        frames.append(
            pd.DataFrame(
                {
                    "time": t,
                    "quality": np.zeros(t.size, "i4"),
                    "mom_centr1": c1,
                    "mom_centr2": 500 + rng.normal(0, 0.002, t.size),
                    "sector": sec,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def test_centroid_empirical_errors_tolerate_red_noise():
    """B5: correlated centroid jitter no longer fakes an offset (white errors failed 2-47 %)."""
    from planethunter.vetting.basic import _centroid_test

    fails = 0
    for seed in range(8):
        raw = _centroid_raw({1: 0.0}, red=0.004, seed=seed)
        tr = _centroid_test(raw, P, T0, 2.8 / 24, CFG, 300e-6, SUN)
        fails += tr.passed is False
    assert fails <= 1


def test_centroid_per_sector_and_crowdsap():
    from planethunter.vetting.basic import _centroid_test

    # Opposite shifts in two sectors (different CCD frames) would cancel if pooled.
    raw = _centroid_raw({10: 0.01, 11: -0.01})
    tr = _centroid_test(raw, P, T0, 2.8 / 24, CFG, 2000e-6, SUN)
    assert tr.passed is False and "s10" in tr.note and "s11" in tr.note
    # delta_ap = CROWDSAP x delta: a crowded aperture implies a source farther away.
    raw = _centroid_raw({1: 0.001})
    full = _centroid_test(raw, P, T0, 2.8 / 24, CFG, 2000e-6, SUN)
    crowded = StarParams(tic_id=1, radius_rsun=1.0, mass_msun=1.0, crowdsap=0.5)
    half = _centroid_test(raw, P, T0, 2.8 / 24, CFG, 2000e-6, crowded)
    assert half.value == pytest.approx(2 * full.value, rel=1e-6)


def test_centroid_indeterminate_when_saturated_or_few_transits():
    """Kostov+2019: centroid offsets from 2-3 transits or saturated stars are indeterminate."""
    from planethunter.vetting.basic import _centroid_test

    raw = _centroid_raw({1: 0.01})
    bright = StarParams(tic_id=1, radius_rsun=1.0, mass_msun=1.0, tmag=6.0)
    assert _centroid_test(raw, P, T0, 2.8 / 24, CFG, 2000e-6, bright).passed is None
    short = _centroid_raw({1: 0.01}, n_days=8.0)  # 2 transits
    tr = _centroid_test(short, P, T0, 2.8 / 24, CFG, 2000e-6, SUN)
    assert tr.passed is None and "indeterminate" in tr.note


def test_weaker_sibling_alias_is_not_masked_but_unrelated_one_is():
    """G7: mask weaker siblings, except aliases (they may be the same system's secondary)."""
    sig, lc, raw = make(secondary=1500e-6)
    rep = vet_signal(sig, lc, raw, SUN, CFG, weaker_signals=[(P, T0 + P / 2, sig.duration_days)])
    assert "secondary" in rep.vetoed_by  # the EB secondary stays visible
    # A weaker planet at an unrelated period whose transits land on phase 0.5.
    sig, lc, raw = make()
    p2, t02 = 1.5 * P, T0 + P / 2
    ph2 = ((lc.time - t02 + 0.5 * p2) % p2) - 0.5 * p2
    lc.flux[np.abs(ph2) < sig.duration_days / 2] -= np.float32(1500e-6)
    unmasked = vet_signal(sig, lc, raw, SUN, CFG)
    masked = vet_signal(sig, lc, raw, SUN, CFG, weaker_signals=[(p2, t02, sig.duration_days)])
    assert unmasked.test("secondary").passed is False
    assert masked.test("secondary").passed is True
    assert "1 weaker signal(s) masked" in masked.test("independence").note


def test_snr_pink_gate_veto_soft_and_missing():
    """S/N_pink (QLP): veto when configured, soft fail otherwise, NULL never vetoes."""
    sig, lc, raw = make()
    rep = vet_signal(sig, lc, raw, SUN, CFG)
    pink = rep.test("snr_pink")
    assert pink.passed is None and not pink.veto and rep.verdict == "PASS_BASIC"
    clean_score = rep.score  # NULL snr_pink (old runs) costs no unknown_weight
    sig.snr_pink = 25.0
    assert vet_signal(sig, lc, raw, SUN, CFG).score == pytest.approx(clean_score)
    sig.snr_pink = 5.0
    veto_cfg = CFG.model_copy(update={"snr_pink_veto": True})
    assert "snr_pink" in vet_signal(sig, lc, raw, SUN, veto_cfg).vetoed_by
    soft_cfg = CFG.model_copy(update={"snr_pink_veto": False})
    rep = vet_signal(sig, lc, raw, SUN, soft_cfg)
    assert "snr_pink" in rep.failed and "snr_pink" not in rep.vetoed_by


def _batman_lc(k, b, cad_min=2.0, a_rs=10.0, noise=300e-6, seed=0, u=(0.40, 0.20)):
    import batman

    rng = np.random.default_rng(seed)
    t = np.arange(1325.0, 1352.0, cad_min / 1440)
    p = batman.TransitParams()
    p.t0, p.per, p.rp, p.a = T0, P, k, a_rs
    p.inc = float(np.degrees(np.arccos(b / a_rs)))
    p.ecc, p.w, p.limb_dark, p.u = 0.0, 90.0, "quadratic", list(u)
    kw = {"supersample_factor": 30, "exp_time": cad_min / 1440} if cad_min > 2 else {}
    f = batman.TransitModel(p, t, **kw).light_curve(p)
    f = f + rng.normal(0, noise * np.sqrt(2.0 / cad_min), t.size)
    ph = ((t - T0 + 0.5 * P) % P) - 0.5 * P
    t14 = P / np.pi * np.arcsin(np.sqrt((1 + k) ** 2 - b**2) / a_rs / np.sin(np.radians(p.inc)))
    return t, f, ph, t14


def test_supersample_factor_follows_kipping_2010b():
    from planethunter.vetting.ldfit import supersample_factor

    assert supersample_factor(2 / 1440, 2.0) == 1
    assert supersample_factor(20 / 86400, 2.0) == 1
    assert supersample_factor(200 / 86400, 2.0) == 2
    assert supersample_factor(10 / 1440, 2.0) == 5
    assert supersample_factor(30 / 1440, 2.0) == 15


@pytest.mark.parametrize("cad_min", [2.0, 30.0])
def test_limb_darkened_fit_recovers_k_and_b(cad_min):
    from planethunter.vetting.ldfit import cadence_per_point, fit_transit_ld

    u = (0.40, 0.20)
    t, f, ph, t14 = _batman_lc(0.1, 0.4, cad_min=cad_min, u=u)
    fit = fit_transit_ld(
        ph, f, P, 0.01, t14, u, sigma=None, exptime_days=cadence_per_point(t, None)
    )
    assert fit is not None and not fit["unconstrained"]
    assert fit["k"] == pytest.approx(0.1, abs=0.005)
    # 30-min data barely constrains b; the Occam tie-break then keeps the lowest b.
    assert fit["b"] == pytest.approx(0.4, abs=0.15) if cad_min == 2.0 else fit["b"] < 0.55
    assert fit["t14_days"] == pytest.approx(t14, rel=0.05)
    assert fit["supersample"] == (15 if cad_min == 30.0 else 1)


def test_kdr25_grazing_fails_and_radius_uses_ld_k():
    t, f, ph, t14 = _batman_lc(0.15, 1.0, noise=200e-6)
    lc = FlatLightCurve(t, f.astype("f4"), np.full(t.size, 2e-4, "f4"), np.ones(t.size, "i2"))
    sig = VetSignal(P, T0, t14, 1e6 * (1 - f[np.abs(ph) < 0.01].mean()), 20, 30, 7)
    rep = vet_signal(sig, lc, None, SUN, CFG)
    kd = rep.test("kdr25_grazing")
    assert kd.passed is False and kd.value > CFG.kdr25_max, kd.note
    assert "grazing" in rep.test("radius").note  # k degenerate: sqrt(depth) lower bound

    t, f, ph, t14 = _batman_lc(0.1, 0.3, noise=200e-6)
    lc = FlatLightCurve(t, f.astype("f4"), np.full(t.size, 2e-4, "f4"), np.ones(t.size, "i2"))
    sig = VetSignal(P, T0, t14, 1e6 * (1 - f[np.abs(ph) < 0.01].mean()), 20, 30, 7)
    rep = vet_signal(sig, lc, None, SUN, CFG)
    assert rep.test("kdr25_grazing").passed is True
    assert "limb-darkened fit" in rep.test("radius").note
    # sqrt(depth) is biased by limb darkening (high by ~5-10 % at low b); the LD k is not.
    assert rep.fit["rp_rs"] == pytest.approx(0.1, abs=0.005)
    assert rep.fit["ld_k"] == pytest.approx(0.1, abs=0.005)
    off = vet_signal(sig, lc, None, SUN, CFG.model_copy(update={"ld_fit_enabled": False}))
    assert off.test("kdr25_grazing").passed is None and "ld_k" not in off.fit
