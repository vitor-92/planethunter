"""Signal statistics recomputed outside TLS. Pure functions on arrays; no disk, no network.

Why: TLS 2.0 reports `duration` multiplied by the fill factor of the series (fraction of
cadences present over the whole span). In multi-sector runs with sectors years apart the
fill factor is ~0.07, so a 3 h transit came out as 0.2 h, and everything that used it (SNR,
iterative mask, alias refinement, vetting windows) was wrong (audit A5). Here T14 is restored
and the white SNR, the pink SNR (Pont et al. 2006) and the count of observed transits are
measured with it.

Units: time in BTJD (days), durations in days, flux dimensionless (~1.0).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def tls_fill_factor(t: np.ndarray) -> float:
    """TLS fill factor: (N - 1) / (span / median cadence). Same formula as TLS 2.0 stats."""
    if len(t) < 2:
        return 1.0
    cadence = float(np.median(np.diff(t)))
    span = float(t[-1] - t[0])
    if not (cadence > 0 and span > 0):
        return 1.0
    return min(1.0, (len(t) - 1) / (span / cadence))


def physical_duration(tls_duration_days: float, t: np.ndarray) -> float:
    """T14 (days) from TLS `duration`: undo the fill-factor multiplication TLS applies.

    `t` must be the exact time array TLS was given. TLS computes
    duration = template_width * stretch * period * fill(t); dividing by fill(t) gives back the
    full width (first to fourth contact) of the limb-darkened template that fit best.
    """
    fill = tls_fill_factor(t)
    return float(tls_duration_days / fill) if fill > 0 else float("nan")


def _phase(t: np.ndarray, period: float, t0: float) -> np.ndarray:
    """Time from the nearest mid-transit (days), in [-P/2, P/2)."""
    return (t - t0 + 0.5 * period) % period - 0.5 * period


def _mad_std(x: np.ndarray) -> float:
    if len(x) == 0:
        return float("nan")
    return float(1.4826 * np.median(np.abs(x - np.median(x))))


@dataclass(frozen=True)
class BoxStats:
    snr: float  # depth / sigma * sqrt(n_in)
    depth: float  # flux fraction (positive = dip)
    sigma: float  # robust point scatter out of transit (flux fraction)
    n_in: int  # points within +-T14/2


def white_snr(t: np.ndarray, f: np.ndarray, period: float, t0: float, t14_days: float) -> BoxStats:
    """White-noise S/N of a box: in-transit mean over |phase| < T14/2 against the robust (MAD)
    scatter of the points with |phase| > T14 (same out-of-transit mask width as TLS)."""
    bad = BoxStats(0.0, float("nan"), float("nan"), 0)
    if len(t) < 10 or not (period > 0 and t14_days > 0):
        return bad
    ph = np.abs(_phase(t, period, t0))
    inn = ph < 0.5 * t14_days
    out = ph > t14_days
    if inn.sum() == 0 or out.sum() < 10:
        return bad
    base = float(np.median(f[out]))
    sigma = _mad_std(f[out])
    depth = base - float(np.mean(f[inn]))
    n_in = int(inn.sum())
    snr = depth / sigma * math.sqrt(n_in) if sigma > 0 else 0.0
    return BoxStats(float(snr), depth, sigma, n_in)


def pink_snr(t: np.ndarray, f: np.ndarray, period: float, t0: float, t14_days: float) -> float:
    """S/N with red noise on the T14 time scale (Pont, Zucker & Queloz 2006, MNRAS 373, 231).

    sigma_w = robust (MAD) point scatter out of transit; sigma_n = std of the means of T14-long
    bins out of transit; sigma_r^2 = max(sigma_n^2 - sigma_w^2 / n, 0). Each transit i
    with n_i points has variance sigma_w^2 / n_i + sigma_r^2; the combined S/N is the
    inverse-variance weighted mean depth over its error. With equal transits this equals
    sqrt(sum_i snr_pink_i^2) and depth / sqrt(sigma_w^2 / N_in + sigma_r^2 / N_tr) (QLP S/N_pink).
    """
    if len(t) < 20 or not (period > 0 and t14_days > 0):
        return float("nan")
    ph = _phase(t, period, t0)
    inn = np.abs(ph) < 0.5 * t14_days
    out = np.abs(ph) > t14_days
    if inn.sum() == 0 or out.sum() < 20:
        return float("nan")
    t_out, f_out = t[out], f[out]
    base = float(np.median(f_out))
    sigma_w = _mad_std(f_out)
    if not (sigma_w > 0):
        return float("nan")
    cadence = float(np.median(np.diff(t)))
    n_nom = max(1.0, t14_days / cadence) if cadence > 0 else 1.0
    idx = np.floor((t_out - t_out[0]) / t14_days).astype(np.int64)
    _, start, counts = np.unique(idx, return_index=True, return_counts=True)
    means = np.add.reduceat(f_out, start) / counts
    full = counts >= 0.8 * n_nom
    sigma_r2 = 0.0
    if full.sum() >= 10:
        # Plain std: red-noise excursions are exactly what sigma_r must capture.
        sigma_n = float(np.std(means[full]))
        n_bar = float(np.mean(counts[full]))
        sigma_r2 = max(sigma_n**2 - sigma_w**2 / n_bar, 0.0)
    epoch = np.round((t[inn] - t0) / period).astype(np.int64)
    order = np.argsort(epoch, kind="stable")
    _, start_i, n_i = np.unique(epoch[order], return_index=True, return_counts=True)
    f_in = f[inn][order]
    depth_i = base - np.add.reduceat(f_in, start_i) / n_i
    w = 1.0 / (sigma_w**2 / n_i + sigma_r2)
    return float(np.sum(w * depth_i) / math.sqrt(np.sum(w)))


def observed_epochs(
    t: np.ndarray,
    period: float,
    t0: float,
    t14_days: float,
    *,
    min_coverage: float = 0.5,
    max_subbins: int = 200,
) -> np.ndarray:
    """Mid-transit times (BTJD) of epochs with data over >= min_coverage of [-T14/2, +T14/2].

    Coverage = fraction of sub-intervals (each >= the median cadence) that contain data.
    """
    if len(t) < 2 or not (period > 0 and t14_days > 0):
        return np.empty(0)
    cadence = float(np.median(np.diff(t)))
    m = int(np.clip(math.floor(t14_days / cadence), 1, max_subbins)) if cadence > 0 else 1
    n = np.round((t - t0) / period).astype(np.int64)
    ph = t - (t0 + n * period)
    sel = np.abs(ph) < 0.5 * t14_days
    if not sel.any():
        return np.empty(0)
    sub = np.clip(np.floor((ph[sel] / t14_days + 0.5) * m).astype(np.int64), 0, m - 1)
    pairs = np.unique(n[sel] * (m + 1) + sub)
    epochs, filled = np.unique(pairs // (m + 1), return_counts=True)
    keep = epochs[filled / m >= min_coverage]
    return t0 + keep.astype(np.float64) * period
