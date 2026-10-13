"""Basic vetting of a signal: tests that only need the light curve and the star (no network).

Numbering follows docs/PLAN.md §6. Tests 9 (TPF difference image), 10 (Gaia neighbors) and
13 (FPP with triceratops) need the network and live in deep vetting; here test 9 has an
offline version using the per-cadence centroids (MOM_CENTR) from the SPOC file itself.

Verdict (audit B6, 2026-10-10): FAIL if any test vetoes, if any test listed in
`vetting.hard_fail_tests` fails, or if more than `vetting.max_soft_fails` tests fail softly;
otherwise PASS_BASIC. The multiplicative score (weights in config) is only used for ranking.

Period halving (audit A7): a signal found at twice the true period shows the in-between
transit as a "secondary" at phase 0.5 with the same depth and duration. In that case the
signal is re-vetted at P/2 (same t0) and the report carries a `period_halved` test whose value
is the vetted period. Twin EBs are then caught at P/2 by odd-even, shape, radius or duration.

S/N_pink (QLP, Guerrero et al. 2021; Kunimoto et al. 2022, 2023) is a detection gate next to
sde/snr/n_transits; whether it vetoes is `vetting.snr_pink_veto`. Signals from runs that
predate signals.snr_pink get passed=None (never a veto, no unknown-weight penalty).

A limb-darkened batman fit (vetting/ldfit.py) complements the trapezoid: its k = Rp/R* feeds
the radius test (non-grazing fits; grazing k is degenerate with b and sqrt(depth) is used as a
lower bound) and the soft `kdr25_grazing` test (k + b > kdr25_max, KDR25, Thompson et al.
2018). The trapezoid tau/T14 shape test is unchanged.

Conventions: time in BTJD, period and duration in days internally, depth as a fraction.
Each test returns a TestResult; insufficient data -> passed=None, never an exception.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, replace

import numpy as np
import pandas as pd
from scipy import optimize, stats

from planethunter.config import VettingConfig
from planethunter.models import LOGG_SUN_CGS, StarParams
from planethunter.preprocess.clean import FlatLightCurve, quality_bitmask
from planethunter.vetting.ldfit import cadence_per_point, fit_transit_ld

R_EARTH_PER_R_SUN = 109.076
G_SI = 6.674e-11
M_SUN_KG = 1.98847e30
R_SUN_M = 6.957e8
DESAT_BIT = 32  # TessQualityFlags.Desat (momentum dump)
DEEP_TESTS = ("tpf_difference_image", "gaia_neighbors", "fpp_triceratops")


@dataclass
class TestResult:
    name: str
    value: float | None
    threshold: float | None
    passed: bool | None
    veto: bool = False
    note: str = ""
    # Machine-readable details for downstream stages (e.g. FPP validation-region flags).
    extra: dict = field(default_factory=dict)


@dataclass
class VetSignal:
    """The minimum the vetting needs from a signal. Units: days, BTJD, ppm."""

    period_days: float
    t0_btjd: float
    duration_days: float
    depth_ppm: float
    sde: float
    snr: float
    n_transits: int
    edge_transit_fraction: float = 0.0
    snr_pink: float | None = None  # signals.snr_pink (Pont 2006 on T14); None for old runs


@dataclass
class VettingReport:
    tests: list[TestResult]
    score: float
    verdict: str  # PASS_BASIC | FAIL
    vetoed_by: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    deep_pending: tuple[str, ...] = DEEP_TESTS
    # Trapezoid depth_ppm, t14_hours, tau_frac; rp_rs = k used by the radius test; ld_* = batman.
    fit: dict = field(default_factory=dict)
    period_days: float | None = None  # period actually vetted (P/2 if `period_halved`)

    def test(self, name: str) -> TestResult:
        return next(t for t in self.tests if t.name == name)

    def to_rows(self) -> list[dict]:
        return [asdict(t) for t in self.tests]


# ---------------------------------------------------------------- utilities


def phase_days(t: np.ndarray, period: float, t0: float) -> np.ndarray:
    """Distance (days) to the nearest transit, in [-P/2, P/2)."""
    return ((t - t0 + 0.5 * period) % period) - 0.5 * period


def epoch_index(t: np.ndarray, period: float, t0: float) -> np.ndarray:
    return np.round((t - t0) / period).astype(np.int64)


def _robust_sigma(x: np.ndarray) -> float:
    if len(x) < 5:
        return float("nan")
    return float(1.4826 * np.median(np.abs(x - np.median(x))))


def trapezoid(t: np.ndarray, depth: float, t14: float, tau: float, center: float) -> np.ndarray:
    """Symmetric trapezoid in flux fraction. t14 total, tau = duration of each ramp (days)."""
    x = np.abs(t - center)
    half = t14 / 2
    tau = np.clip(tau, 1e-6, half)
    flat = half - tau
    m = np.ones_like(t)
    m[x <= flat] = 1 - depth
    ramp = (x > flat) & (x < half)
    m[ramp] = 1 - depth * (half - x[ramp]) / tau
    return m


def _fit_trapezoid_once(
    ph: np.ndarray, f: np.ndarray, depth0: float, dur0: float, sigma: float | None
) -> dict | None:
    sel = np.abs(ph) < 2 * dur0
    if sel.sum() < 20:
        return None
    x, y = ph[sel], f[sel]
    # soft_l1 only down-weights outliers if f_scale is the residual scale (sigma_white);
    # with the default f_scale=1 it is plain least squares (audit, Tier C).
    if sigma is None or not np.isfinite(sigma) or sigma <= 0:
        sigma = _robust_sigma(y[np.abs(x) > 0.75 * dur0])
    if not np.isfinite(sigma) or sigma <= 0:
        sigma = _robust_sigma(y)
    f_scale = float(sigma) if np.isfinite(sigma) and sigma > 0 else 1.0

    def resid(p: np.ndarray) -> np.ndarray:
        return trapezoid(x, p[0], p[1], p[2] * p[1], p[3]) - y

    p0 = [max(depth0, 1e-5), dur0, 0.15, 0.0]
    lo = [0.0, 0.2 * dur0, 0.01, -0.3 * dur0]
    hi = [0.9, 3.0 * dur0, 0.5, 0.3 * dur0]
    try:
        r = optimize.least_squares(resid, p0, bounds=(lo, hi), loss="soft_l1", f_scale=f_scale)
    except (ValueError, RuntimeError):
        return None
    depth, t14, tau_frac, center = r.x
    return {
        "depth": float(depth),
        "t14_days": float(t14),
        "tau_frac": float(tau_frac),
        "center_days": float(center),
        "rp_rs": float(math.sqrt(max(depth, 0.0))),
        "t14_at_upper": bool(t14 >= 0.99 * hi[1]),
        "t14_at_lower": bool(t14 <= 1.01 * lo[1]),
    }


def fit_trapezoid(
    ph: np.ndarray, f: np.ndarray, depth0: float, dur0: float, sigma: float | None = None
) -> dict | None:
    """Trapezoid fit to the folded curve (|phase| < 2 durations). None on failure.

    `sigma` = white noise of `f` (sets the soft_l1 scale). T14 is bounded to 0.2-3 x dur0; a
    fit at the upper bound is retried once with dur0 doubled. If T14 still sits on a bound the
    fit carries `t14_at_bound=True`: T14 (and tau/T14) are unconstrained, not measured.
    Measured in sector 107: 467 NEW signals sat at the 3 x duration bound.
    """
    fit = _fit_trapezoid_once(ph, f, depth0, dur0, sigma)
    if fit is not None and fit["t14_at_upper"]:
        wide = _fit_trapezoid_once(ph, f, depth0, 2.0 * dur0, sigma)
        if wide is not None and not wide["t14_at_upper"]:
            fit = wide
    if fit is not None:
        upper, lower = fit.pop("t14_at_upper"), fit.pop("t14_at_lower")
        fit["t14_at_bound"] = bool(upper or lower)
    return fit


def stellar_logg(star: StarParams) -> float | None:
    """log g (cgs) from the TIC, or from TIC mass and radius; None if neither is available."""
    if star.logg_cgs is not None and np.isfinite(star.logg_cgs):
        return float(star.logg_cgs)
    m, r = star.mass_msun, star.radius_rsun
    if m and r and np.isfinite(m) and np.isfinite(r) and m > 0 and r > 0:
        return LOGG_SUN_CGS + math.log10(m / r**2)
    return None


def predicted_duration_days(period: float, star: StarParams, rp_rs: float = 0.0) -> float | None:
    """T14 for b = 0, circular orbit: (P/pi) * (1 + k) / (a/R*)."""
    r = star.radius_rsun
    m = star.mass_or_estimate()
    if not (r and m and r > 0 and m > 0):
        return None
    rho = m * M_SUN_KG / (4 / 3 * math.pi * (r * R_SUN_M) ** 3)
    p_s = period * 86400.0
    a_rs = (G_SI * rho * p_s**2 / (3 * math.pi)) ** (1 / 3)
    if a_rs <= 1 + rp_rs:
        return None
    return period / math.pi * math.asin(min(1.0, (1 + rp_rs) / a_rs))


def _alias_related(p_other: float, period: float, tol: float = 0.01, kmax: int = 4) -> bool:
    """True if p_other / period is close to k or 1/k (k = 1..kmax)."""
    r = p_other / period
    return any(abs(r / k - 1) < tol or abs(r * k - 1) < tol for k in range(1, kmax + 1))


# ---------------------------------------------------------------- tests


class BlockNoise:
    """Error of the mean of n consecutive points, measured out of transit (includes red noise).

    sigma_n = max(sigma / sqrt(n), std of the means of n-point blocks). Pont et al. 2006.
    Measured in sector 69: with sigma/sqrt(n), 4 of 41 confirmed planets failed the
    transit-to-transit consistency test.
    """

    def __init__(self, f_out: np.ndarray):
        self.f = f_out
        self.white = _robust_sigma(f_out)
        self._cache: dict[int, float] = {}

    def err(self, n: float) -> float:
        n = max(1, int(round(n)))
        if n not in self._cache:
            white = self.white / math.sqrt(n)
            m = len(self.f) // n
            if m >= 5:
                blocks = self.f[: m * n].reshape(m, n).mean(axis=1)
                self._cache[n] = max(white, float(np.std(blocks, ddof=1)))
            else:
                self._cache[n] = white
        return self._cache[n]


def _box_depth(
    f: np.ndarray, mask: np.ndarray, base: float, noise: BlockNoise, n_ep: np.ndarray
) -> tuple[float, float, int]:
    """Mean depth over the `mask` points; error uses block noise per epoch."""
    n = int(mask.sum())
    if n < 3:
        return float("nan"), float("nan"), n
    k = max(1, len(np.unique(n_ep[mask])))
    return base - float(np.mean(f[mask])), noise.err(n / k) / math.sqrt(k), n


def vet_signal(
    sig: VetSignal,
    lc: FlatLightCurve,
    raw: pd.DataFrame | None,
    star: StarParams | None,
    cfg: VettingConfig,
    *,
    other_signals: list[tuple[float, float, float]] = (),
    weaker_signals: list[tuple[float, float, float]] = (),
    allow_halving: bool = True,
) -> VettingReport:
    """Run the basic tests.

    `other_signals` = (P [d], t0 [BTJD], duration [d]) of STRONGER signals on the target: masked
    before every test and used by the independence test. `weaker_signals` = the other signals
    on the target: also masked (audit G7: a weaker planet's transit must not create a fake
    secondary or odd-even difference), except those whose period is an alias (k or 1/k) of
    this one, which may be this system's own secondary eclipse, and except echoes (masking
    them would remove > 50 % of this signal's in-transit points). `raw` = concatenated
    ingestion Parquet (time, quality, mom_centr1/2; optional `sector` column).
    """
    star = star or StarParams(tic_id=0)
    P, t0, dur = sig.period_days, sig.t0_btjd, sig.duration_days
    t, f = lc.time, lc.flux.astype(np.float64)
    keep = np.ones(len(t), dtype=bool)
    for p2, t02, d2 in other_signals:
        keep &= np.abs(phase_days(t, p2, t02)) > 1.5 * d2
    core_all = np.abs(phase_days(t, P, t0)) < 0.4 * dur
    kept_frac = float(keep[core_all].mean()) if core_all.any() else 1.0
    n_weak_masked = 0
    for p2, t02, d2 in weaker_signals:
        if _alias_related(p2, P):
            continue
        m = np.abs(phase_days(t, p2, t02)) > 1.5 * d2
        if core_all.any() and (keep & m)[core_all].sum() < 0.5 * keep[core_all].sum():
            continue  # echo of this signal: masking it would remove the transit itself
        keep &= m
        n_weak_masked += 1
    t, f = t[keep], f[keep]

    ph = phase_days(t, P, t0)
    n_ep = epoch_index(t, P, t0)
    core = np.abs(ph) < 0.4 * dur
    out = np.abs(ph) > 1.5 * dur
    base = float(np.median(f[out])) if out.sum() > 10 else 1.0
    noise = BlockNoise(f[out]) if out.sum() > 10 else BlockNoise(f)
    tests: list[TestResult] = []

    # 1-3 detection: mandatory gates (docs/PLAN.md §6). Failure = veto.
    # Measured in sector 69: as a soft penalty, signals with SNR 4.9 and with a single transit
    # became P2.
    for name, value, thr in (
        ("sde", sig.sde, cfg.sde_min),
        ("snr", sig.snr, cfg.snr_min),
        ("n_transits", sig.n_transits, cfg.min_transits),
    ):
        ok = value >= thr
        tests.append(TestResult(name, value, thr, ok, veto=not ok))
    tests.append(_snr_pink_test(sig.snr_pink, cfg))

    # Independence: if masking stronger signals on the target removes the transit, it's a duplicate.
    # Measured in sector 69: signal 1601 (11.95 d) reused the eclipses of 1600 (6.75 d).
    tests.append(
        TestResult(
            "independence",
            kept_frac,
            0.5,
            kept_frac >= 0.5,
            veto=kept_frac < 0.5,
            note=f"{kept_frac:.0%} of in-transit points remain after masking stronger signals"
            + (f"; {n_weak_masked} weaker signal(s) masked" if n_weak_masked else ""),
        )
    )

    # 6 (fit first: the period-halving check needs the primary T14)
    # soft_l1 scale = trapezoid_f_scale_sigma x sigma_white; 0 = plain least squares (f_scale 1).
    mult = cfg.trapezoid_f_scale_sigma
    sigma_w = noise.white / base * mult if base > 0 and mult > 0 else (1.0 if mult <= 0 else None)
    fit = fit_trapezoid(ph, f / base, sig.depth_ppm * 1e-6, dur, sigma_w)
    ld = None
    if cfg.ld_fit_enabled:
        ld = fit_transit_ld(
            ph,
            f / base,
            P,
            fit["depth"] if fit else sig.depth_ppm * 1e-6,
            dur,
            _limb_darkening(star),
            sigma=noise.white / base if base > 0 else None,
            exptime_days=cadence_per_point(t, lc.sector[keep] if len(lc.sector) else None),
            subexposure_minutes=cfg.ld_fit_subexposure_minutes,
            f_scale_sigma=cfg.trapezoid_f_scale_sigma,
            delta_chi2=cfg.ld_fit_delta_chi2,
            t14_0=fit["t14_days"] if fit and not fit.get("t14_at_bound") else None,
            center0=fit["center_days"] if fit else 0.0,
        )

    # 4 odd-even
    d_odd, e_odd, n_odd = _box_depth(f, core & (n_ep % 2 == 1), base, noise, n_ep)
    d_even, e_even, n_even = _box_depth(f, core & (n_ep % 2 == 0), base, noise, n_ep)
    if np.isfinite(d_odd) and np.isfinite(d_even):
        z = abs(d_odd - d_even) / math.hypot(e_odd, e_even)
        tests.append(
            TestResult(
                "odd_even",
                z,
                cfg.odd_even_fail_sigma,
                z < cfg.odd_even_fail_sigma,
                veto=z > cfg.odd_even_veto_sigma,
                note=f"odd {d_odd * 1e6:.0f} ppm, even {d_even * 1e6:.0f} ppm",
            )
        )
    else:
        tests.append(
            TestResult(
                "odd_even",
                None,
                cfg.odd_even_fail_sigma,
                None,
                note=f"odd/even points: {n_odd}/{n_even}",
            )
        )

    # 5 secondary eclipse at phase 0.5. Epochs by floor((t - t0)/P): the box centred on
    # phase 0.5 must not be split in two at the rounding boundary (audit, Tier C).
    ph2 = ((t - t0) % P) - 0.5 * P
    ep_sec = np.floor((t - t0) / P).astype(np.int64)
    sec_mask = np.abs(ph2) < 0.4 * dur
    d_sec, e_sec, n_sec = _box_depth(f, sec_mask, base, noise, ep_sec)
    if np.isfinite(d_sec):
        s = d_sec / e_sec
        d_prim, e_prim, _ = _box_depth(f, core, base, noise, n_ep)
        ratio = d_sec / d_prim if d_prim > 0 else float("inf")

        # A7: same depth and duration at phase 0.5 = the in-between transit of a signal found
        # at 2P (TOI-431 b was vetoed this way). Re-vet at P/2.
        if allow_halving and s >= cfg.secondary_fail_sigma and np.isfinite(d_prim):
            halved = _try_halving(
                sig, lc, raw, star, cfg, t, f, ph2, core, sec_mask, base, fit, sigma_w,
                (d_sec, e_sec, d_prim, e_prim), other_signals, weaker_signals,
            )  # fmt: skip
            if halved is not None:
                return halved

        # A planetary occultation (e.g. WASP-18 b, ~340 ppm) is small relative to the transit;
        # an EB secondary is usually a large fraction of the primary. Veto only if both.
        tests.append(
            TestResult(
                "secondary",
                s,
                cfg.secondary_fail_sigma,
                s < cfg.secondary_fail_sigma,
                veto=s > cfg.secondary_veto_sigma and ratio >= cfg.secondary_veto_ratio,
                note=f"{d_sec * 1e6:.0f} ppm at phase 0.5 ({ratio:.0%} of primary)",
            )
        )
    else:
        tests.append(
            TestResult(
                "secondary",
                None,
                cfg.secondary_fail_sigma,
                None,
                note=f"{n_sec} points at phase 0.5",
            )
        )

    # 5b secondary at any phase (eccentric EB: TOI-367.01 used to pass)
    tests.append(_secondary_scan_test(t, f, P, t0, dur, base, noise, cfg))

    # 6 shape (trapezoid)
    unconstrained = bool(fit and fit.get("t14_at_bound"))
    if fit is not None:
        v_ok = fit["tau_frac"] <= cfg.v_shape_max
        k_ok = fit["rp_rs"] <= cfg.rp_rs_max
        passed: bool | None = v_ok and k_ok
        note = f"tau/T14 {fit['tau_frac']:.2f}, Rp/R* {fit['rp_rs']:.3f}"
        if unconstrained and k_ok:
            passed = None
            note += "; T14 on its fit bound: shape unconstrained"
        tests.append(TestResult("shape", fit["tau_frac"], cfg.v_shape_max, passed, note=note))
    else:
        n_near = int((np.abs(ph) < 2 * dur).sum())
        # With enough data, a trapezoid that fails to fit is suspicious (signal 1601, SNR 22).
        tests.append(
            TestResult(
                "shape",
                None,
                cfg.v_shape_max,
                False if n_near >= 20 else None,
                note=f"trapezoid fit failed ({n_near} points near transit)",
            )
        )

    # 6b grazing (KDR25 k + b cut) from the limb-darkened fit
    tests.append(_kdr25_test(ld, cfg))

    # 7 radius: k from the limb-darkened fit when it is constrained and not grazing
    depth = fit["depth"] if fit else sig.depth_ppm * 1e-6
    k_used, k_src = _radius_k(ld, depth)
    tests.append(_radius_test(depth, star, fit, tests, cfg, k=k_used, k_source=k_src))

    # 8 duration vs stellar density
    t14 = fit["t14_days"] if fit else dur
    t_pred = predicted_duration_days(P, star, fit["rp_rs"] if fit else 0.0)
    if t_pred and unconstrained:
        tests.append(
            TestResult(
                "duration",
                None,
                cfg.duration_ratio_max,
                None,
                note=f"trapezoid T14 {t14 * 24:.2f} h is on its fit bound (unconstrained; "
                f"ratio would be {t14 / t_pred:.2f}); predicted (b=0) {t_pred * 24:.2f} h",
            )
        )
    elif t_pred:
        ratio = t14 / t_pred
        tests.append(
            TestResult(
                "duration",
                ratio,
                cfg.duration_ratio_max,
                cfg.duration_ratio_min <= ratio <= cfg.duration_ratio_max,
                note=f"T14 {t14 * 24:.2f} h vs predicted (b=0) {t_pred * 24:.2f} h",
            )
        )
    else:
        tests.append(TestResult("duration", None, cfg.duration_ratio_max, None, note="no R*/M*"))

    # 9 (offline) per-cadence centroid
    tests.append(_centroid_test(raw, P, t0, dur, cfg, depth, star))

    # 11 segment edges and momentum dumps
    tests.append(_edges_dumps_test(raw, t, n_ep, core, P, t0, sig.edge_transit_fraction, cfg))

    # 12 transit-to-transit consistency
    tests.append(_consistency_test(f, n_ep, core, base, noise, cfg))

    rep = _score(tests, cfg, fit, ld=ld, k_used=k_used)
    rep.period_days = P
    return rep


def _limb_darkening(star: StarParams) -> tuple[float, float]:
    """Claret (2017) TESS quadratic u for the star; Sun-like (5750 K, log g 4.44) without Teff."""
    from planethunter.search.tls import tess_limb_darkening

    teff = star.teff_k if star.teff_k and np.isfinite(star.teff_k) else 5750.0
    return tess_limb_darkening(teff, stellar_logg(star) or LOGG_SUN_CGS)


def _snr_pink_test(value: float | None, cfg: VettingConfig) -> TestResult:
    """Detection gate on S/N_pink (QLP: Guerrero et al. 2021; Kunimoto et al. 2022, 2023).

    Vetoes on failure only if `vetting.snr_pink_veto`; NULL (runs older than the column) gives
    passed=None and never vetoes.
    """
    name, thr = "snr_pink", cfg.snr_pink_min
    if value is None or not np.isfinite(value):
        return TestResult(name, None, thr, None, note="snr_pink not stored (run predates it)")
    ok = bool(value >= thr)
    note = "" if ok else ("veto" if cfg.snr_pink_veto else "soft fail (snr_pink_veto: false)")
    return TestResult(name, float(value), thr, ok, veto=not ok and cfg.snr_pink_veto, note=note)


def _kdr25_test(ld: dict | None, cfg: VettingConfig) -> TestResult:
    """Grazing cut k + b > kdr25_max (Kepler DR25, Thompson et al. 2018). Soft fail.

    passed=None without a constrained limb-darkened fit (k or T14 on a bound, fit failed).
    """
    name, thr = "kdr25_grazing", cfg.kdr25_max
    if ld is None:
        why = "disabled" if not cfg.ld_fit_enabled else "too few points near transit"
        return TestResult(name, None, thr, None, note=f"no limb-darkened fit ({why})")
    if ld.get("unconstrained"):
        note = f"limb-darkened fit unconstrained: {ld.get('reason')}"
        return TestResult(name, None, thr, None, note=note, extra=ld)
    v = ld["k"] + ld["b"]
    note = (
        f"k {ld['k']:.3f} +- {ld['k_err']:.3f}, b {ld['b']:.2f} +- {ld['b_err']:.2f}, "
        f"a/R* {ld['a_rs']:.1f}, T14 {ld['t14_days'] * 24:.2f} h, depth {ld['depth'] * 1e6:.0f} "
        f"ppm (u {ld['u'][0]:.2f}, {ld['u'][1]:.2f}; supersample {ld['supersample']})"
    )
    return TestResult(name, float(v), thr, bool(v <= thr), note=note, extra=ld)


def _radius_k(ld: dict | None, depth: float) -> tuple[float | None, str]:
    """k for the radius test: the limb-darkened k of a constrained full transit (k + b <= 1);
    otherwise sqrt(trapezoid depth) (a grazing k is degenerate with b; sqrt(depth) is a lower
    bound)."""
    sq = math.sqrt(depth) if depth > 0 else None
    if ld is None or ld.get("unconstrained"):
        return sq, "sqrt(trapezoid depth)"
    if ld["k"] + ld["b"] > 1.0:
        return sq, "sqrt(depth); grazing LD fit, k degenerate with b"
    return float(ld["k"]), "limb-darkened fit"


def _try_halving(
    sig: VetSignal,
    lc: FlatLightCurve,
    raw: pd.DataFrame | None,
    star: StarParams,
    cfg: VettingConfig,
    t: np.ndarray,
    f: np.ndarray,
    ph2: np.ndarray,
    core: np.ndarray,
    sec_mask: np.ndarray,
    base: float,
    fit: dict | None,
    sigma_w: float | None,
    depths: tuple[float, float, float, float],
    other_signals,
    weaker_signals,
) -> VettingReport | None:
    """Re-vet at P/2 if the phase-0.5 dip matches the primary in depth and duration.

    Depth: |d_sec - d_prim| / sqrt(e_sec^2 + e_prim^2) < halving_max_depth_sigma.
    Duration: trapezoid T14 at phase 0.5 within halving_duration_tol of the primary T14
    (skipped, with a note, when either fit is unavailable or unconstrained).
    """
    d_sec, e_sec, d_prim, e_prim = depths
    z = abs(d_sec - d_prim) / math.hypot(e_sec, e_prim)
    if not np.isfinite(z) or z >= cfg.halving_max_depth_sigma:
        return None
    P, dur = sig.period_days, sig.duration_days
    fit_sec = fit_trapezoid(ph2, f / base, d_sec, dur, sigma_w)
    if (
        fit is not None
        and fit_sec is not None
        and not fit.get("t14_at_bound")
        and not fit_sec.get("t14_at_bound")
    ):
        dratio = fit_sec["t14_days"] / fit["t14_days"]
        if abs(dratio - 1) > cfg.halving_duration_tol:
            return None
        dnote = f"T14 ratio {dratio:.2f}"
    else:
        dnote = "T14 not comparable (fit unconstrained), depth only"
    n_new = int(core.sum() + sec_mask.sum())
    snr_scale = math.sqrt(n_new / core.sum()) if core.sum() else 1.0
    ep_half = epoch_index(t[core | sec_mask], P / 2, sig.t0_btjd)
    n_tr = len(np.unique(ep_half))
    sig2 = replace(
        sig,
        period_days=P / 2,
        snr=sig.snr * snr_scale,
        snr_pink=sig.snr_pink * snr_scale if sig.snr_pink is not None else None,
        n_transits=max(n_tr, sig.n_transits),
    )
    rep = vet_signal(
        sig2,
        lc,
        raw,
        star,
        cfg,
        other_signals=other_signals,
        weaker_signals=weaker_signals,
        allow_halving=False,
    )
    rep.tests.insert(
        0,
        TestResult(
            "period_halved",
            P / 2,
            cfg.halving_max_depth_sigma,
            True,
            note=(
                f"dip at phase 0.5 ({d_sec * 1e6:.0f} ppm) matches the primary "
                f"({d_prim * 1e6:.0f} ppm; {z:.1f} sigma; {dnote}): re-vetted at P/2 = "
                f"{P / 2:.5f} d (found at {P:.5f} d; SNR x{snr_scale:.2f}, {n_tr} transits)"
            ),
            extra={"period_found_days": P, "period_vetted_days": P / 2, "depth_sigma": z},
        ),
    )
    rep.period_days = P / 2
    return rep


def _radius_test(
    depth: float,
    star: StarParams,
    fit: dict | None,
    tests: list[TestResult],
    cfg: VettingConfig,
    *,
    k: float | None = None,
    k_source: str = "sqrt(trapezoid depth)",
) -> TestResult:
    """Rp = k R*: k = limb-darkened Rp/R* when given, else sqrt(depth) (PDCSAP depth is
    already crowding-corrected).

    Veto only with a reliable R* (TIC radius and log g >= radius_veto_min_logg) AND another EB
    sign (V shape, odd-even or secondary failure): Mullally et al. 2015 argue against declaring
    false positives from the inferred radius alone. Otherwise a large radius is a soft fail.
    """
    name = "radius"
    if k is None and depth > 0:
        k = math.sqrt(depth)
    if not (star.radius_rsun and k and k > 0):
        return TestResult(name, None, cfg.radius_fail_rearth, None, note="no R* or depth")
    rp = k * star.radius_rsun * R_EARTH_PER_R_SUN
    logg = stellar_logg(star)
    reliable = logg is not None and logg >= cfg.radius_veto_min_logg
    by = {tr.name: tr for tr in tests}
    signs = [n for n in ("odd_even", "secondary") if n in by and by[n].passed is False]
    if fit is not None and not fit.get("t14_at_bound") and fit["tau_frac"] > cfg.v_shape_max:
        signs.append("V shape")
    veto = rp > cfg.radius_veto_rearth and reliable and bool(signs)
    note = (
        f"Rp = {rp:.1f} R_earth (k {k:.3f} from {k_source}; R* {star.radius_rsun:.2f}; "
        "PDCSAP corrects crowding)"
    )
    if rp > cfg.radius_veto_rearth and not veto:
        why = "R* unreliable (log g " + (f"{logg:.2f})" if logg is not None else "unknown)")
        note += f"; veto withheld: {why if not reliable else 'no other EB sign'}"
    elif veto:
        note += f"; EB signs: {', '.join(signs)}"
    return TestResult(name, rp, cfg.radius_fail_rearth, rp < cfg.radius_fail_rearth, veto=veto,
                      note=note)  # fmt: skip


def _secondary_scan_test(
    t: np.ndarray,
    f: np.ndarray,
    P: float,
    t0: float,
    dur: float,
    base: float,
    noise: BlockNoise,
    cfg: VettingConfig,
) -> TestResult:
    """Deepest dip with the transit duration at phases 0.1-0.9, away from the vicinity of 0.5."""
    name = "secondary_scan"
    phase = ((t - t0) / P) % 1.0
    half = 0.4 * dur / P
    best_s, best_phi, best_d = -np.inf, float("nan"), float("nan")
    step = max(half, 0.002)
    for phi in np.arange(0.1, 0.9 + 1e-9, step):
        if abs(phi - 0.5) < 2 * half:
            continue  # phase 0.5 already covered by the `secondary` test
        mask = np.abs(phase - phi) < half
        # Epoch boundary half a period away from the box centre (audit, Tier C).
        ep = np.floor((t - t0) / P - phi + 0.5).astype(np.int64)
        d, e, n = _box_depth(f, mask, base, noise, ep)
        if n >= 3 and np.isfinite(d) and e > 0 and d / e > best_s:
            best_s, best_phi, best_d = d / e, phi, d
    if not np.isfinite(best_s):
        return TestResult(
            name, None, cfg.secondary_scan_fail_sigma, None, note="no out-of-transit data"
        )
    return TestResult(
        name,
        float(best_s),
        cfg.secondary_scan_fail_sigma,
        best_s < cfg.secondary_scan_fail_sigma,
        note=f"deepest dip {best_d * 1e6:.0f} ppm ({best_s:.1f} sigma) at phase {best_phi:.3f}",
    )


def _epoch_shift(
    t: np.ndarray, cx: np.ndarray, cy: np.ndarray, center: float, dur: float
) -> tuple[float, float, float, float] | None:
    """Centroid shift (in - local linear baseline) around `center`; (dx, dy, ex, ey) in px.

    `t` must be sorted. In: |t - center| < 0.4 dur; baseline: 1 < |t - center|/dur < 3.
    The errors (ex, ey) are white-noise errors of the in-transit mean.
    """
    lo, hi = np.searchsorted(t, [center - 3.0 * dur, center + 3.0 * dur])
    if hi - lo < 13:
        return None
    tt = t[lo:hi] - center
    a = np.abs(tt)
    inn = a < 0.4 * dur
    loc = (a > 1.0 * dur) & (a < 3.0 * dur)
    if inn.sum() < 3 or loc.sum() < 10:
        return None
    tm = tt[inn].mean()
    out = []
    for c in (cx[lo:hi], cy[lo:hi]):
        coef = np.polyfit(tt[loc] - tm, c[loc], 1)
        resid = c[loc] - np.polyval(coef, tt[loc] - tm)
        out.append((float(np.mean(c[inn]) - coef[1]), float(np.std(resid) / math.sqrt(inn.sum()))))
    return out[0][0], out[1][0], out[0][1], out[1][1]


def _centroid_test(
    raw: pd.DataFrame | None,
    P: float,
    t0: float,
    dur: float,
    cfg: VettingConfig,
    depth: float,
    star: StarParams | None = None,
) -> TestResult:
    """In-transit centroid shift (MOM_CENTR) and implied source distance (pixels), per sector.

    A source at distance D from the flux centroid, with depth delta_ap in the aperture flux,
    shifts the centroid by ~ delta_ap * D, so D_impl = shift / delta_ap, with
    delta_ap = CROWDSAP * delta (PDCSAP depths are crowding-corrected; MOM_CENTR is not).

    Significance is empirical (audit B5): the same per-epoch estimator is run at up to
    `centroid_null_epochs` fake out-of-transit epochs per sector; their robust scatter is the
    per-epoch error (never below the white-noise error). With white-noise errors, random
    epochs failed 2-47 % of the time against 1 % expected. MOM_CENTR is in CCD pixels, whose
    orientation changes between sectors, so each sector is evaluated on its own and the
    chi-square values are summed. Indeterminate (passed=None, Kostov et al. 2019) for
    saturated stars (Tmag < centroid_min_tmag) or sectors with < centroid_min_transits transits.
    Fails only if significant (>= centroid_fail_sigma) AND D_impl > centroid_max_offset_px.
    """
    name = "centroid"
    if raw is None or not {"mom_centr1", "mom_centr2", "quality"} <= set(raw.columns):
        return TestResult(name, None, cfg.centroid_fail_sigma, None, note="no centroids")
    star = star or StarParams(tic_id=0)
    if star.tmag is not None and np.isfinite(star.tmag) and star.tmag < cfg.centroid_min_tmag:
        return TestResult(
            name,
            None,
            cfg.centroid_max_offset_px,
            None,
            note=f"Tmag {star.tmag:.1f} < {cfg.centroid_min_tmag:g}: saturated, MOM_CENTR "
            "unreliable (indeterminate)",
        )
    crowd = star.crowdsap if star.crowdsap and 0 < star.crowdsap <= 1 else 1.0
    depth_ap = depth * crowd
    ok = (
        np.isfinite(raw["mom_centr1"].to_numpy())
        & np.isfinite(raw["mom_centr2"].to_numpy())
        & ((raw["quality"].to_numpy() & quality_bitmask("default")) == 0)
    )
    df = raw.loc[ok]
    sectors = df["sector"].to_numpy() if "sector" in df.columns else np.zeros(len(df), int)
    rng = np.random.default_rng(12345)
    chi2_tot, dof, parts, impl_w, n_used = 0.0, 0, [], [], 0
    n_short = 0
    for sec in np.unique(sectors):
        d = df[sectors == sec].sort_values("time")
        t = d["time"].to_numpy()
        cx, cy = d["mom_centr1"].to_numpy(float), d["mom_centr2"].to_numpy(float)
        ph = phase_days(t, P, t0)
        ep = epoch_index(t, P, t0)
        real = []
        for e in np.unique(ep[np.abs(ph) < 0.4 * dur]):
            r = _epoch_shift(t, cx, cy, t0 + e * P, dur)
            if r is not None:
                real.append(r)
        if len(real) < cfg.centroid_min_transits:
            n_short += len(real) > 0
            continue
        # Fake epochs: centres whose whole window stays away from the real transits.
        cand = np.arange(t[0] + 3 * dur, t[-1] - 3 * dur, 2 * dur)
        cand = cand[np.abs(phase_days(cand, P, t0)) > 3.5 * dur]
        if len(cand) > cfg.centroid_null_epochs:
            cand = rng.choice(cand, cfg.centroid_null_epochs, replace=False)
        fake = [r for c in cand if (r := _epoch_shift(t, cx, cy, c, dur)) is not None]
        s = np.array(real)
        white = np.median(s[:, 2:], axis=0)
        if len(fake) >= 20:
            fk = np.array(fake)[:, :2]
            emp = np.array([_robust_sigma(fk[:, 0]), _robust_sigma(fk[:, 1])])
            per_ep = np.maximum(emp, white)
            how = f"{len(fake)} fake epochs"
        else:
            per_ep = white
            how = "white noise (too few fake epochs)"
        k = len(real)
        mean = s[:, :2].mean(axis=0)
        err = per_ep / math.sqrt(k)
        chi2 = float(np.sum((mean / err) ** 2))
        chi2_tot += chi2
        dof += 2
        shift = float(math.hypot(*mean))
        impl = shift / depth_ap if depth_ap > 0 else float("inf")
        impl_w.append((impl, k))
        n_used += k
        z_s = max(0.0, float(stats.norm.isf(max(stats.chi2.sf(chi2, 2), 1e-300))))
        parts.append(
            f"s{int(sec)}: shift {shift * 1000:.1f} mpx ({z_s:.1f} sigma, {how}), "
            f"{k} transits, implied {impl:.2f} px"
        )
    if dof == 0:
        why = (
            f"fewer than {cfg.centroid_min_transits} transits with centroids per sector"
            if n_short
            else "no epochs with centroids"
        )
        return TestResult(
            name, None, cfg.centroid_max_offset_px, None, note=f"{why} (indeterminate)"
        )
    z = max(0.0, float(stats.norm.isf(max(stats.chi2.sf(chi2_tot, dof), 1e-300))))
    implied = sum(i * k for i, k in impl_w) / sum(k for _, k in impl_w)
    off_target = z >= cfg.centroid_fail_sigma and implied > cfg.centroid_max_offset_px
    return TestResult(
        name,
        implied,
        cfg.centroid_max_offset_px,
        not off_target,
        note=(
            f"combined {z:.1f} sigma over {n_used} transits; implied source {implied:.2f} px "
            f"from centroid (delta_ap = CROWDSAP {crowd:.2f} x depth; indicative, TPF pending) | "
            + "; ".join(parts)
        ),
        extra={"sigma": z},
    )


def _edges_dumps_test(
    raw: pd.DataFrame | None,
    t: np.ndarray,
    n_ep: np.ndarray,
    core: np.ndarray,
    P: float,
    t0: float,
    edge_fraction: float,
    cfg: VettingConfig,
) -> TestResult:
    name = "edges_dumps"
    epochs = np.unique(n_ep[core])
    if len(epochs) == 0:
        return TestResult(name, None, cfg.max_dump_transit_fraction, None, note="no epochs")
    centers = t0 + epochs * P
    dump_frac = 0.0
    if raw is not None and "quality" in raw:
        dumps = raw["time"].to_numpy()[(raw["quality"].to_numpy() & DESAT_BIT) != 0]
        if len(dumps):
            near = np.min(np.abs(centers[:, None] - dumps[None, :]), axis=1) < cfg.dump_window_days
            dump_frac = float(near.mean())
    worst = max(dump_frac, edge_fraction)
    return TestResult(
        name,
        worst,
        cfg.max_dump_transit_fraction,
        worst <= cfg.max_dump_transit_fraction,
        note=f"at momentum dump {dump_frac:.0%}, at segment edge {edge_fraction:.0%}",
    )


def _consistency_test(
    f: np.ndarray,
    n_ep: np.ndarray,
    core: np.ndarray,
    base: float,
    noise: BlockNoise,
    cfg: VettingConfig,
) -> TestResult:
    name = "consistency"
    depths, errs = [], []
    for e in np.unique(n_ep[core]):
        d, err, n = _box_depth(f, core & (n_ep == e), base, noise, n_ep)
        if n >= 3 and np.isfinite(d):
            depths.append(d)
            errs.append(err)
    if len(depths) < 2:
        return TestResult(
            name,
            None,
            cfg.transit_consistency_pvalue_min,
            None,
            note=f"{len(depths)} transit(s) with data",
        )
    d, e = np.array(depths), np.array(errs)
    mean = np.sum(d / e**2) / np.sum(1 / e**2)
    chi2 = float(np.sum(((d - mean) / e) ** 2))
    p = float(stats.chi2.sf(chi2, len(d) - 1))
    snr2 = (d / e) ** 2
    dominance = float(snr2.max() / snr2.sum()) if snr2.sum() > 0 else 1.0
    dominated = len(d) >= 3 and dominance > 0.8
    return TestResult(
        name,
        p,
        cfg.transit_consistency_pvalue_min,
        p >= cfg.transit_consistency_pvalue_min and not dominated,
        note=f"{len(d)} transits, chi2 p = {p:.3g}, strongest transit = {dominance:.0%} of SNR²",
    )


def _score(
    tests: list[TestResult],
    cfg: VettingConfig,
    fit: dict | None,
    *,
    ld: dict | None = None,
    k_used: float | None = None,
) -> VettingReport:
    """Score (ranking) and verdict.

    score = product of the weights of the failed tests x unknown_weight per test without data;
    0 if any veto. Tests in `unknown_exempt_tests` are not penalized when passed is None
    (snr_pink missing in runs that predate it; kdr25_grazing without a constrained LD fit,
    already paid for by the duration test). Verdict (audit B6): FAIL on any veto, on any
    failure of a test listed in `hard_fail_tests`, or on more than `max_soft_fails` soft
    failures; else PASS_BASIC.
    Measured before the change: 5 confirmed planets failed on a single soft test because any
    weight <= 0.5 pushed the score below pass_score.
    """
    score = 1.0
    vetoed, failed = [], []
    for tr in tests:
        if tr.veto:
            vetoed.append(tr.name)
        elif tr.passed is False:
            failed.append(tr.name)
            score *= cfg.weights.get(tr.name, 0.5)
        elif tr.passed is None and tr.name not in cfg.unknown_exempt_tests:
            score *= cfg.unknown_weight
    if vetoed:
        score = 0.0
    hard = [n for n in failed if n in cfg.hard_fail_tests]
    verdict = "FAIL" if vetoed or hard or len(failed) > cfg.max_soft_fails else "PASS_BASIC"
    fit_out = {}
    if fit:
        fit_out = {
            "depth_ppm": fit["depth"] * 1e6,
            "t14_hours": fit["t14_days"] * 24,
            "tau_frac": fit["tau_frac"],
            "rp_rs": fit["rp_rs"],
            "t14_at_bound": bool(fit.get("t14_at_bound", False)),
        }
    if k_used is not None:
        fit_out["rp_rs"] = float(k_used)
    if ld and not ld.get("unconstrained"):
        fit_out |= {
            "ld_k": ld["k"],
            "ld_b": ld["b"],
            "ld_a_rs": ld["a_rs"],
            "ld_t14_hours": ld["t14_days"] * 24,
            "ld_depth_ppm": ld["depth"] * 1e6,
        }
    return VettingReport(tests, score, verdict, vetoed, failed, DEEP_TESTS, fit_out)
