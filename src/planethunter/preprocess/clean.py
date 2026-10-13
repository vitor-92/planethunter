"""Cleaning and detrending. Pure functions on arrays; no disk, no network.

Rules:
- Outliers are clipped only upwards. Clipping downwards removes transits.
- Detrending with wotan biweight; the window must be ~3x the longest duration searched,
  otherwise the filter eats the transit (Hippke et al. 2019, AJ 158, 143).
- Each sector is normalized and detrended separately, then concatenated. The window used for
  each sector is kept in `FlatLightCurve.windows` ({sector: window_days}).
- flux_err is divided by the trend, like the flux.
- When re-detrending a known signal (vetting), its transits are masked so the trend is
  interpolated across them and the depth is not eaten (`flatten_for_signal`).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from planethunter.config import PreprocessConfig

# lightkurve "default" bitmask for TESS (TessQualityFlags.DEFAULT_BITMASK = 17087 in
# lightkurve 2.x): AttitudeTweak, SafeMode, CoarsePoint, EarthPoint, Argabrightening,
# Desat (momentum dump), ManualExclude, ImpulsiveOutlier, BadCalibrationExclude.
# ApertureCosmic, CollateralCosmic, Straylight and ScatteredLight are NOT in the default mask.
# Resolved at runtime to track the installed version.
_BITMASK_CACHE: dict[str, int] = {}


def quality_bitmask(name: str) -> int:
    if name == "none":
        return 0
    if name not in _BITMASK_CACHE:
        from lightkurve.utils import TessQualityFlags

        _BITMASK_CACHE[name] = {
            "default": TessQualityFlags.DEFAULT_BITMASK,
            "hard": TessQualityFlags.HARD_BITMASK,
            "hardest": TessQualityFlags.HARDEST_BITMASK,
        }[name]
    return _BITMASK_CACHE[name]


@dataclass
class FlatLightCurve:
    """Normalized, detrended light curve. time in BTJD; dimensionless flux (~1.0)."""

    time: np.ndarray  # float64
    flux: np.ndarray  # float32
    flux_err: np.ndarray  # float32
    sector: np.ndarray  # int16, sector of each point
    window_days: float = float("nan")  # smallest detrending window across sectors (days)
    windows: dict[int, float] = field(default_factory=dict)  # {sector: window_days}

    def __len__(self) -> int:
        return len(self.time)

    @property
    def span_days(self) -> float:
        return float(self.time[-1] - self.time[0]) if len(self) else 0.0

    @property
    def sectors(self) -> list[int]:
        return sorted({int(s) for s in np.unique(self.sector)})

    def windows_json(self) -> str:
        """Per-sector windows as JSON ({"sector": window_days}), stored on every signal."""
        return json.dumps({str(k): float(v) for k, v in sorted(self.windows.items())})


def _upper_clip(flux: np.ndarray, sigma: float) -> np.ndarray:
    """Mask True = keep. Removes only points above median + sigma * robust MAD."""
    med = np.nanmedian(flux)
    mad = 1.4826 * np.nanmedian(np.abs(flux - med))
    if not np.isfinite(mad) or mad == 0:
        return np.ones_like(flux, dtype=bool)
    return flux <= med + sigma * mad


def _mad_std(x: np.ndarray) -> float:
    """Robust standard deviation, 1.4826 * MAD (dimensionless, same units as x)."""
    if len(x) == 0:
        return float("nan")
    return float(1.4826 * np.median(np.abs(x - np.median(x))))


def red_noise_ratio(
    flux: np.ndarray, time: np.ndarray | None = None, *, bin_hours: float = 0.0
) -> float:
    """Robust red-noise ratio: ~1 for white noise, > 1 for residual variability.

    Default (bin_hours <= 0 or no `time`): MAD(flux) / point-to-point MAD, the robust version
    of the old std/p2p ratio (same calibration of red_noise_max). With `time` (BTJD) and
    bin_hours > 0: Pont et al. 2006 beta on `bin_hours` bins, robust (MAD) scatter of the bin
    means against sigma_w / sqrt(n_bin). Measured on 300 sector 69 targets (2026-10-10): ratio
    > 1.2 for 18.7 % (old std), 16.0 % (MAD), 41 % (1 h beta: hour-scale red noise is common).

    Robust estimators matter: with np.std a deep transit inflates the scatter, so the adaptive
    window selection rewarded windows short enough to eat the transit (audit B2).
    """
    flux = np.asarray(flux, dtype=np.float64)
    if len(flux) < 10:
        return float("nan")
    sigma_w = _mad_std(np.diff(flux)) / math.sqrt(2.0)
    if not (sigma_w > 0):
        return float("nan")
    if time is None or not bin_hours > 0:
        return _mad_std(flux) / sigma_w
    time = np.asarray(time, dtype=np.float64)
    cadence = float(np.median(np.diff(time)))
    width = bin_hours / 24.0
    n_nominal = width / cadence if cadence > 0 else 0.0
    if n_nominal < 2:
        return _mad_std(flux) / sigma_w
    idx = np.floor((time - time[0]) / width).astype(np.int64)
    _, start, counts = np.unique(idx, return_index=True, return_counts=True)
    means = np.add.reduceat(flux, start) / counts
    ok = counts >= 0.5 * n_nominal  # partial bins at gaps would add white noise only
    if ok.sum() < 10:
        return _mad_std(flux) / sigma_w
    z = (means[ok] - np.median(means[ok])) * np.sqrt(counts[ok]) / sigma_w
    return _mad_std(z)


def flatten_adaptive(
    df: pd.DataFrame,
    sector: int,
    cfg: PreprocessConfig,
    *,
    first: FlatLightCurve | None = None,
) -> FlatLightCurve:
    """Detrend with the default window; if red noise remains, try smaller windows.

    A smaller window removes fast variability but eats long transits, so it is only used
    when the default leaves residuals. Keeps the first window below red_noise_max, or the
    one with the lowest (robust) ratio.
    """
    best: FlatLightCurve | None = None
    best_ratio = float("inf")
    for w in [cfg.window_length_days, *cfg.fallback_windows_days]:
        if first is not None and w == cfg.window_length_days:
            lc = first  # already computed by the caller (avoids redoing the default window)
        else:
            lc = flatten_sector(df, sector, cfg.model_copy(update={"window_length_days": w}))
        if len(lc) == 0:
            return lc
        ratio = red_noise_ratio(
            lc.flux.astype(np.float64), lc.time, bin_hours=cfg.red_noise_bin_hours
        )
        if ratio < best_ratio:
            best, best_ratio = lc, ratio
        if ratio <= cfg.red_noise_max:
            break
    return best if best is not None else _empty()


def _ephemeris_mask(
    t: np.ndarray, ephemerides: list[tuple[float, float, float]] | None
) -> np.ndarray | None:
    """True inside any transit window. ephemerides = [(period_d, t0_btjd, width_d)]."""
    if not ephemerides:
        return None
    m = np.zeros(len(t), dtype=bool)
    for period, t0, width in ephemerides:
        if period > 0 and width > 0 and np.isfinite(period + t0 + width):
            m |= np.abs((t - t0 + 0.5 * period) % period - 0.5 * period) < 0.5 * width
    return m if m.any() else None


def flatten_sector(
    df: pd.DataFrame,
    sector: int,
    cfg: PreprocessConfig,
    *,
    mask_ephemerides: list[tuple[float, float, float]] | None = None,
) -> FlatLightCurve:
    """One sector's light curve (ingest Parquet columns) -> FlatLightCurve.

    mask_ephemerides: [(period_d, t0_btjd, width_d)] excluded from the trend estimate (wotan
    mask); the trend is interpolated across them, so a known transit keeps its depth.
    """
    from wotan import flatten  # lazy import: numba compiles on the first call

    t = df["time"].to_numpy(np.float64)
    f = df["flux"].to_numpy(np.float64)
    e = df["flux_err"].to_numpy(np.float64)
    q = df["quality"].to_numpy(np.int64)

    good = np.isfinite(t) & np.isfinite(f) & np.isfinite(e) & (f > 0)
    bitmask = quality_bitmask(cfg.quality_bitmask)
    if bitmask:
        good &= (q & bitmask) == 0
    t, f, e = t[good], f[good], e[good]
    if len(t) < cfg.min_points:
        return _empty()

    med = np.median(f)
    f, e = f / med, e / med

    keep = _upper_clip(f, cfg.sigma_upper)
    t, f, e = t[keep], f[keep], e[keep]

    flat, trend = flatten(
        t,
        f,
        method=cfg.detrend_method,
        window_length=cfg.window_length_days,
        edge_cutoff=cfg.edge_cutoff_days,
        break_tolerance=cfg.break_tolerance_days,
        return_trend=True,
        mask=_ephemeris_mask(t, mask_ephemerides),
    )
    ok = np.isfinite(flat) & np.isfinite(trend) & (trend > 0)
    # Clip upwards again: flares only become evident after detrending.
    ok &= _upper_clip(np.where(ok, flat, np.nan), cfg.sigma_upper)
    t, flat, e, trend = t[ok], flat[ok], e[ok], trend[ok]
    e = e / trend  # same normalization as the flux
    if len(t) < cfg.min_points:
        return _empty()
    return FlatLightCurve(
        time=t,
        flux=flat.astype(np.float32),
        flux_err=e.astype(np.float32),
        sector=np.full(len(t), sector, dtype=np.int16),
        window_days=cfg.window_length_days,
        windows={int(sector): float(cfg.window_length_days)},
    )


def signal_windows(
    windows_json: str | None,
    fallback_window_days: float | None,
    duration_days: float,
    sectors: list[int],
    cfg: PreprocessConfig,
) -> dict[int, float]:
    """Detrending window per sector for re-detrending a signal (vetting, dossier, FPP).

    Uses the window each sector had at search time (signals.detrend_windows_json); falls back
    to signals.detrend_window_days, then to the default window. Never below
    cfg.min_window_durations x T14 (Hippke et al. 2019: window ~3x the transit duration).
    """
    try:
        stored = {int(k): float(v) for k, v in json.loads(windows_json or "{}").items()}
    except (TypeError, ValueError):
        stored = {}
    fb = fallback_window_days
    fb = cfg.window_length_days if fb is None or not np.isfinite(fb) else float(fb)
    floor = cfg.min_window_durations * duration_days if duration_days > 0 else 0.0
    out = {}
    for s in sectors:
        w = stored.get(int(s), fb)
        w = cfg.window_length_days if not (np.isfinite(w) and w > 0) else w
        out[int(s)] = float(max(w, floor))
    return out


def flatten_for_signal(
    frames: list[tuple[pd.DataFrame, int]],
    cfg: PreprocessConfig,
    *,
    windows: dict[int, float],
    period_days: float,
    t0_btjd: float,
    duration_days: float,
    mask_half_phase: bool = True,
) -> FlatLightCurve:
    """Re-detrend all sectors for one signal: each sector with its own window and the signal's
    transits masked (width cfg.signal_mask_width_durations x T14), then stitch.

    mask_half_phase: also mask phase 0.5 (the P/2 ephemeris), so a transit in between (signal
    found at 2P, re-vetted at P/2 by the `period_halved` test) or a secondary eclipse is not
    eaten before vetting measures it.
    """
    width = cfg.signal_mask_width_durations * duration_days
    ephem = None
    if width > 0:
        ephem = [(period_days, t0_btjd, width)]
        if mask_half_phase:
            ephem.append((period_days, t0_btjd + 0.5 * period_days, width))
    parts = []
    for df, s in frames:
        w = windows.get(int(s), cfg.window_length_days)
        pre = cfg.model_copy(update={"window_length_days": w})
        parts.append(flatten_sector(df, s, pre, mask_ephemerides=ephem))
    return stitch(parts)


def stitch(parts: list[FlatLightCurve]) -> FlatLightCurve:
    parts = [p for p in parts if len(p)]
    if not parts:
        return _empty()
    order = np.argsort([p.time[0] for p in parts])
    parts = [parts[i] for i in order]
    windows: dict[int, float] = {}
    for p in parts:
        windows.update(p.windows)
    return FlatLightCurve(
        time=np.concatenate([p.time for p in parts]),
        flux=np.concatenate([p.flux for p in parts]),
        flux_err=np.concatenate([p.flux_err for p in parts]),
        sector=np.concatenate([p.sector for p in parts]),
        window_days=float(min(p.window_days for p in parts)),
        windows=windows,
    )


def bin_lightcurve(lc: FlatLightCurve, minutes: float) -> FlatLightCurve:
    """Binning into fixed `minutes` boxes. Empty boxes are dropped (gaps preserved).

    Bin error = sqrt(sum(e^2)) / n. Never crosses sector boundaries.
    """
    if minutes <= 0 or len(lc) == 0:
        return lc
    width = minutes / 1440.0
    idx = np.floor((lc.time - lc.time[0]) / width).astype(np.int64)
    key = idx * 10_000 + lc.sector.astype(np.int64)  # separates sectors in the same box
    order = np.argsort(key, kind="stable")
    key_s = key[order]
    starts = np.flatnonzero(np.r_[True, key_s[1:] != key_s[:-1]])
    counts = np.diff(np.r_[starts, len(key_s)])

    def _mean(x: np.ndarray) -> np.ndarray:
        return np.add.reduceat(x[order].astype(np.float64), starts) / counts

    t = _mean(lc.time)
    f = _mean(lc.flux)
    e = np.sqrt(np.add.reduceat(lc.flux_err[order].astype(np.float64) ** 2, starts)) / counts
    s = lc.sector[order][starts]
    o = np.argsort(t)
    return FlatLightCurve(
        time=t[o],
        flux=f[o].astype(np.float32),
        flux_err=e[o].astype(np.float32),
        sector=s[o],
        window_days=lc.window_days,
        windows=dict(lc.windows),
    )


def _empty() -> FlatLightCurve:
    return FlatLightCurve(
        time=np.empty(0, np.float64),
        flux=np.empty(0, np.float32),
        flux_err=np.empty(0, np.float32),
        sector=np.empty(0, np.int16),
    )
