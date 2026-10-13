"""Limb-darkened transit fit of the folded light curve (batman, Kreidberg 2015, PASP 127, 1161).

Complements the trapezoid fit of basic vetting (which stays the calibrated shape test): a
quadratic limb-darkened Mandel & Agol (2002) model gives k = Rp/R*, the impact parameter b,
a/R* and T14, which feed the radius test (k instead of sqrt(depth)) and the KDR25-style
grazing cut k + b > 1.04 (`kdr25_grazing`).

- Limb darkening fixed to the Claret (2017) TESS-band quadratic coefficients for the star's
  Teff/logg (same table and lookup as the TLS template, search/tls.py::tess_limb_darkening).
- Circular orbit; free parameters k, beta = b / (1 + k), T14 and the mid-transit offset. a/R*
  follows from (k, b, T14, P): a^2 = ((1 + k)^2 - b^2) / sin^2(pi T14 / P) + b^2, so a >= 1 + k.
- Long exposures smear the transit (Kipping 2010, MNRAS 408, 1758): each cadence group is
  supersampled into sub-exposures no longer than `subexposure_minutes` (2-min data: none;
  200 s: 2; 10 min: 5; 30 min: 15).
- Several starting b; the b-T14-k valley is flat at low S/N, so among solutions whose chi^2 is
  within `delta_chi2` of the best the lowest b is kept (grazing must be preferred by the data).
- `unconstrained=True` when the fit fails, k sits on its upper bound or T14 on a bound: the
  caller then falls back to the trapezoid values.

Units: phase and durations in days, depth as a flux fraction.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from scipy import optimize

K_MAX = 1.0  # k on this bound = V-shaped/EB-like solution, k not measured
BETA_MAX = 0.999
_STARTS_BETA = (0.1, 0.5, 0.85)


def supersample_factor(exptime_days: float, subexposure_minutes: float) -> int:
    """Sub-exposures per cadence (Kipping 2010b): 1 for 2-min data, ceil(exptime / sub) else."""
    minutes = exptime_days * 1440.0
    if not (np.isfinite(minutes) and minutes > 0 and subexposure_minutes > 0):
        return 1
    if minutes <= 1.25 * subexposure_minutes:
        return 1
    return int(math.ceil(minutes / subexposure_minutes))


def cadence_per_point(t: np.ndarray, sector: np.ndarray | None) -> np.ndarray:
    """Exposure time (days) of each point: median time step of its sector (rounded to 1 s)."""
    t = np.asarray(t, dtype=np.float64)
    out = np.full(len(t), np.nan)
    groups = np.zeros(len(t), dtype=np.int64) if sector is None else np.asarray(sector)
    for s in np.unique(groups):
        m = groups == s
        dt = np.diff(t[m])
        dt = dt[dt > 0]
        if len(dt):
            out[m] = round(float(np.median(dt)) * 86400.0) / 86400.0
    fill = float(np.nanmedian(out)) if np.isfinite(out).any() else 120.0 / 86400.0
    return np.where(np.isfinite(out), out, fill)


def a_rs_from_t14(k: float, b: float, t14_days: float, period_days: float) -> float:
    """a/R* of a circular orbit with T14 (first to fourth contact), k and b."""
    s = math.sin(math.pi * t14_days / period_days)
    return math.sqrt(max((1 + k) ** 2 - b**2, 1e-12) / s**2 + b**2)


class _Model:
    """batman models (one per exposure-time group) evaluated on the folded times."""

    def __init__(self, x: np.ndarray, exptime: np.ndarray, period: float, u, sub_minutes: float):
        import batman

        self.n = len(x)
        self.p = batman.TransitParams()
        self.p.t0, self.p.per, self.p.rp, self.p.a, self.p.inc = 0.0, period, 0.05, 10.0, 90.0
        self.p.ecc, self.p.w, self.p.limb_dark, self.p.u = 0.0, 90.0, "quadratic", list(u)
        self.groups = []
        self.factors = []
        for e in np.unique(exptime):
            idx = np.flatnonzero(exptime == e)
            nss = supersample_factor(float(e), sub_minutes)
            kw = {"supersample_factor": nss, "exp_time": float(e)} if nss > 1 else {}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = batman.TransitModel(self.p, x[idx], **kw)
            self.groups.append((idx, m))
            self.factors.append(nss)
        self.center = batman.TransitModel(self.p, np.array([0.0]))

    def set(self, k: float, b: float, t14: float, tc: float) -> float:
        a = a_rs_from_t14(k, b, t14, self.p.per)
        self.p.rp, self.p.a, self.p.t0 = k, a, tc
        self.p.inc = math.degrees(math.acos(min(1.0, b / a)))
        return a

    def flux(self) -> np.ndarray:
        out = np.empty(self.n)
        for idx, m in self.groups:
            out[idx] = m.light_curve(self.p)
        return out

    def depth_at_center(self) -> float:
        tc = self.p.t0
        self.p.t0 = 0.0
        d = 1.0 - float(self.center.light_curve(self.p)[0])
        self.p.t0 = tc
        return d


def fit_transit_ld(
    ph: np.ndarray,
    f: np.ndarray,
    period_days: float,
    depth0: float,
    dur0: float,
    u: tuple[float, float],
    *,
    sigma: float | None,
    exptime_days: np.ndarray | float,
    subexposure_minutes: float = 2.0,
    f_scale_sigma: float = 1.0,
    delta_chi2: float = 1.0,
    t14_0: float | None = None,
    center0: float = 0.0,
) -> dict | None:
    """Quadratic-LD transit fit of the folded, normalized flux `f` at phase `ph` (days).

    Returns None if there is too little data near transit; otherwise a dict with k, b, a_rs,
    t14_days, depth (flux fraction at mid-transit), center_days, k_err, b_err (Gauss-Newton),
    supersample (max factor used), u, unconstrained (bool) and reason.
    """
    t14_ref = t14_0 if t14_0 and np.isfinite(t14_0) and t14_0 > 0 else dur0
    if not (period_days > 0 and dur0 > 0):
        return None
    win = 2.0 * max(dur0, t14_ref)
    sel = np.abs(ph - center0) < win
    if sel.sum() < 20 or (np.abs(ph[sel] - center0) < 0.5 * t14_ref).sum() < 3:
        return None
    x, y = np.asarray(ph[sel], np.float64), np.asarray(f[sel], np.float64)
    exp = np.broadcast_to(np.asarray(exptime_days, np.float64), ph.shape)[sel]
    if sigma is None or not np.isfinite(sigma) or sigma <= 0:
        out = y[np.abs(x - center0) > 0.75 * t14_ref]
        sigma = float(1.4826 * np.median(np.abs(out - np.median(out)))) if len(out) > 5 else 0.0
    if not (np.isfinite(sigma) and sigma > 0):
        return None
    try:
        model = _Model(x, exp, period_days, u, subexposure_minutes)
    except Exception:  # batman missing or a degenerate time array: no LD fit, no crash
        return None

    lo_t14 = 0.2 * min(dur0, t14_ref)
    hi_t14 = min(3.0 * max(dur0, t14_ref), 0.45 * period_days)
    if hi_t14 <= lo_t14:
        return None
    lo = [1e-3, 0.0, lo_t14, center0 - 0.3 * dur0]
    hi = [K_MAX, BETA_MAX, hi_t14, center0 + 0.3 * dur0]

    def resid(p: np.ndarray) -> np.ndarray:
        k, beta, t14, tc = p
        model.set(k, beta * (1 + k), t14, tc)
        return (model.flux() - y) / sigma

    k0 = float(np.clip(1.05 * math.sqrt(max(depth0, 1e-6)), 0.005, 0.9))
    t0_14 = float(np.clip(t14_ref, lo_t14 * 1.01, hi_t14 * 0.99))
    loss = "soft_l1" if f_scale_sigma > 0 else "linear"
    fscale = f_scale_sigma if f_scale_sigma > 0 else 1.0
    sols = []
    for beta0 in _STARTS_BETA:
        try:
            r = optimize.least_squares(
                resid, [k0, beta0, t0_14, center0], bounds=(lo, hi), loss=loss, f_scale=fscale
            )
        except (ValueError, RuntimeError, ZeroDivisionError):
            continue
        if np.all(np.isfinite(r.x)) and np.isfinite(r.cost):
            sols.append(r)
    if not sols:
        return {"unconstrained": True, "reason": "fit failed", "u": list(u)}
    best_cost = min(s.cost for s in sols)
    # cost = 0.5 sum(rho(z^2)); chi^2 ~ 2 cost for small normalized residuals.
    near = [s for s in sols if 2.0 * (s.cost - best_cost) < delta_chi2]
    r = min(near, key=lambda s: s.x[1] * (1 + s.x[0]))
    k, beta, t14, tc = (float(v) for v in r.x)
    b = beta * (1 + k)
    a_rs = model.set(k, b, t14, tc)
    depth = model.depth_at_center()
    k_err = b_err = float("nan")
    try:
        cov = np.linalg.inv(r.jac.T @ r.jac)
        k_err = float(math.sqrt(max(cov[0, 0], 0.0)))
        b_err = float((1 + k) * math.sqrt(max(cov[1, 1], 0.0)))
    except (np.linalg.LinAlgError, ValueError):
        pass
    reasons = []
    if k >= 0.99 * K_MAX:
        reasons.append("k on its upper bound")
    if t14 >= 0.99 * hi_t14 or t14 <= 1.01 * lo_t14:
        reasons.append("T14 on its bound")
    return {
        "k": k,
        "b": b,
        "a_rs": a_rs,
        "t14_days": t14,
        "depth": depth,
        "center_days": tc,
        "k_err": k_err,
        "b_err": b_err,
        "supersample": int(max(model.factors)),
        "u": [float(u[0]), float(u[1])],
        "unconstrained": bool(reasons),
        "reason": "; ".join(reasons),
    }
