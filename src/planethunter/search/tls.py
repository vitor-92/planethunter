"""Periodic search with Transit Least Squares, iterative with masking.

Pure function: takes FlatLightCurve + StarParams, returns a list of Signal. No network; the
only file read is the TESS limb-darkening table shipped inside the TLS package (cached).

What we take from TLS and what we recompute (audit 2026-10-10, A5/A6/B1/B10/B11):
- period, T0, depth, SDE, FAP, odd/even: from TLS.
- duration: TLS multiplies T14 by the fill factor of the series; we divide it back
  (`duration_raw_hours` keeps the TLS value, `duration_hours` is T14).
- snr: recomputed with T14 (white_snr); after refine_alias, measured on the k*P epochs only.
- snr_pink: Pont 2006 red-noise S/N on the T14 time scale (gated in vetting: `snr_pink`).
- n_transits: epochs with >= min_epoch_coverage of [-T14/2, +T14/2] covered by data.
"""

from __future__ import annotations

import functools
import json
import warnings
from dataclasses import dataclass

import numpy as np

from planethunter.config import SearchConfig
from planethunter.models import Signal, StarParams
from planethunter.preprocess.clean import FlatLightCurve, bin_lightcurve
from planethunter.search.stats import (
    observed_epochs,
    physical_duration,
    pink_snr,
    white_snr,
)

# Ranges accepted by TLS; outside them we fall back to the solar default with wide limits.
_R_RANGE = (0.1, 20.0)
_M_RANGE = (0.08, 10.0)
# Stellar values used for the period grid are capped (see _grid_kwargs).
_GRID_STAR_MAX = 1.5
# TLS derives f_max from a = 3 R_star (grid.py::period_grid).
_TLS_ROCHE_A_RSTAR = 3.0
# TLS 2.0 default quadratic limb darkening (Kepler band, Sun-like star).
_TLS_DEFAULT_U = (0.4804, 0.1867)


def _grid_kwargs(star: StarParams | None, cfg: SearchConfig) -> dict:
    """Stellar parameters for TLS. In TLS 2.0 they only drive the period and duration grids;
    the transit template itself is fixed (per/rp/a/inc defaults) and only u changes it.

    - Period grid upper frequency: TLS uses a >= 3 R*. QLP (Kunimoto et al. 2023) uses
      a >= 2 R*, so R* is scaled by roche_min_a_rstar / 3 and the oversampling by the same
      factor (rounded; exact for OS = 3 and a = 2 R*), which leaves the Ofir (2014) grid density
      A ~ R* / (M*^1/3 * span * OS) unchanged.
    - The grid star is capped at R, M <= 1.5: with the TIC R = 4.06 the grid started at 4.15 d
      and TOI 196.01 (P = 1.16 d) disappeared (the TIC radius may be wrong, or the signal may
      come from a neighbor).
    - Duration grid limits always wide. Measured in the sector 69 benchmark (2026-10-09): +-30 %
      limits on R and M removed from the grid transits shorter than the central one (high b,
      wrong TIC radius). TOI 196.01, 347.01, 386.01 and 2339.01 disappeared; with wide limits
      they show up with SDE 8.6-16.8.
    """
    r = star.radius_rsun if star else None
    m = star.mass_or_estimate() if star else None
    r = r if r is not None and _R_RANGE[0] <= r <= _R_RANGE[1] else 1.0
    m = m if m is not None and _M_RANGE[0] <= m <= _M_RANGE[1] else 1.0
    r_tpl, m_tpl = min(r, _GRID_STAR_MAX), min(max(m, 0.1), _GRID_STAR_MAX)
    scale = cfg.roche_min_a_rstar / _TLS_ROCHE_A_RSTAR
    r_grid = r_tpl * scale
    return dict(
        R_star=r_grid,
        R_star_min=min(0.13, r_grid),  # TIC 12395214 and 65263267 have R < 0.13
        R_star_max=min(_R_RANGE[1], max(3.5, 1.3 * r)),
        M_star=m_tpl,
        M_star_min=min(0.1, m_tpl),
        M_star_max=min(_M_RANGE[1], max(2.0, 1.3 * m)),
        # Integer: TLS's SDE running-median kernel (OS * 30) breaks with a float (TLS 2.0).
        oversampling_factor=max(1, round(cfg.oversampling_factor * scale)),
    )


@functools.lru_cache(maxsize=1)
def _claret_tess_table() -> np.ndarray:
    """Claret (2017) TESS-band quadratic LD table shipped with TLS (ld_claret_tess.csv)."""
    from pathlib import Path

    from transitleastsquares import tls_constants

    return np.genfromtxt(
        Path(tls_constants.resources_dir) / "ld_claret_tess.csv",
        skip_header=1,
        delimiter=",",
        dtype="f8, int32, f8, f8",
        names=["logg", "Teff", "a", "b"],
    )


def tess_limb_darkening(teff_k: float, logg_cgs: float | None = None) -> tuple[float, float]:
    """Claret (2017) TESS-band quadratic (u1, u2): nearest Teff, then nearest logg (default
    4.0), in the table shipped with TLS (same lookup as TLS catalog_info, without the network).
    Also used by the limb-darkened transit fit in vetting (vetting/ldfit.py)."""
    logg = logg_cgs if logg_cgs and np.isfinite(logg_cgs) else 4.0
    ld = _claret_tess_table()
    rows = ld[ld["Teff"] == ld["Teff"][np.abs(ld["Teff"] - teff_k).argmin()]]
    best = rows[np.abs(rows["logg"] - logg).argmin()]
    return float(best["a"]), float(best["b"])


def limb_darkening(star: StarParams | None, cfg: SearchConfig) -> tuple[float, float]:
    """Quadratic (u1, u2) for the TLS template. 'tess': tess_limb_darkening(Teff, logg) of the
    star; otherwise (or without Teff) the TLS default."""
    if cfg.limb_darkening != "tess" or star is None:
        return _TLS_DEFAULT_U
    teff = star.teff_k if star.teff_k and np.isfinite(star.teff_k) else None
    if teff is None:
        return _TLS_DEFAULT_U
    return tess_limb_darkening(teff, star.logg_cgs)


def segment_edges(t: np.ndarray, gap_days: float) -> np.ndarray:
    """Start and end times of each continuous segment (BTJD)."""
    if len(t) == 0:
        return np.empty(0)
    breaks = np.flatnonzero(np.diff(t) > gap_days)
    return np.unique(np.r_[t[0], t[breaks], t[breaks + 1], t[-1]])


def edge_fraction(transit_times: np.ndarray, edges: np.ndarray, window_days: float) -> float:
    """Fraction of transits (with data) whose center is within `window_days` of an edge."""
    if len(transit_times) == 0 or len(edges) == 0:
        return 0.0
    dist = np.min(np.abs(transit_times[:, None] - edges[None, :]), axis=1)
    return float(np.mean(dist < window_days))


@dataclass(frozen=True)
class AliasRefinement:
    factor: int  # true period = factor * TLS period
    period_days: float
    t0_btjd: float
    depth_ppm: float
    epochs_with_data: list[float]
    snr: float = 0.0  # depth_a / sigma * sqrt(n_A) over +-T14/2 of the k*P epochs only


def refine_alias(
    t: np.ndarray,
    f: np.ndarray,
    period: float,
    t0: float,
    duration_days: float,
    *,
    factors: tuple[int, ...] = (3, 2),
    min_points: int = 5,
    nsigma: float = 3.0,
) -> AliasRefinement | None:
    """Test whether the true period is k * P (k in `factors`). duration_days = T14 (days).

    With few transits and data gaps, TLS may prefer P/k: the extra epochs fall into gaps or
    are diluted in the average. For each k and offset j, splits the epochs of P into A
    (predicted by kP) and B (predicted only by P). Accepts kP if A shows a transit (> nsigma)
    and B, with enough data, does not (< nsigma). Measured in sector 69: TOI 899.01, 924.01,
    3262.01 (P ~ 12-13 d) came out as P/3.

    The returned snr is measured on the A epochs only: the TLS SNR averages in the empty
    B epochs and is low by sqrt(n_A / n) (0.58x for k = 3, audit A6).
    """
    if len(t) < 50 or not (period > 0 and duration_days > 0):
        return None
    half = 0.4 * duration_days  # transit core
    n = np.round((t - t0) / period).astype(np.int64)
    intr = np.abs(t - (t0 + n * period)) < half
    out = ~(np.abs(t - (t0 + n * period)) < 1.5 * duration_days)
    if out.sum() < 20:
        return None
    sigma_pt = float(np.std(f[out]))
    base = float(np.median(f[out]))
    for k in factors:
        for j in range(k):
            in_a = intr & (np.mod(n - j, k) == 0)
            in_b = intr & (np.mod(n - j, k) != 0)
            na, nb = int(in_a.sum()), int(in_b.sum())
            if na < min_points or nb < min_points:
                continue
            depth_a = base - float(np.mean(f[in_a]))
            depth_b = base - float(np.mean(f[in_b]))
            err_a, err_b = sigma_pt / np.sqrt(na), sigma_pt / np.sqrt(nb)
            if depth_a > nsigma * err_a and depth_b < nsigma * err_b and depth_a > 3 * depth_b:
                epochs = sorted({float(x) for x in np.unique(n[in_a])})
                t0_a = t0 + j * period
                box = white_snr(t, f, k * period, t0_a, duration_days)
                return AliasRefinement(
                    factor=k,
                    period_days=k * period,
                    t0_btjd=t0_a,
                    depth_ppm=depth_a * 1e6,
                    epochs_with_data=[t0 + e * period for e in epochs],
                    snr=box.snr,
                )
    return None


def _finite(x: object, default: float = float("nan")) -> float:
    try:
        v = float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return v if np.isfinite(v) else default


def _rp_rs(depth_frac: float, u: tuple[float, float]) -> float:
    """Rp/R* from a depth (flux fraction) with quadratic limb darkening (Heller 2019, TLS)."""
    from transitleastsquares.stats import rp_rs_from_depth

    if not (depth_frac > 0):
        return float("nan")
    try:
        return _finite(rp_rs_from_depth(depth=depth_frac, law="quadratic", params=list(u)))
    except (ValueError, ZeroDivisionError):
        return float("nan")


def search_periodic(
    lc: FlatLightCurve,
    star: StarParams | None,
    cfg: SearchConfig,
    *,
    tic_id: int,
    author: str = "SPOC",
    use_threads: int = 1,
) -> list[Signal]:
    """Iterative TLS: find the strongest signal, mask it, repeat.

    Stops when SDE < cfg.sde_keep, when cfg.max_signals_per_target is reached, or when too
    few points remain. Returns signals in detection order (iteration = 0, 1, ...).
    Signal.duration_hours is T14 (hours); Signal.extra carries duration_raw_hours (TLS value),
    snr_pink and detrend_windows_json for the signals table.
    """
    from transitleastsquares import transit_mask, transitleastsquares

    work = bin_lightcurve(lc, cfg.bin_minutes)
    if len(work) < 100 or work.span_days < 2 * cfg.period_min_days:
        return []
    t = work.time.copy()
    f = work.flux.astype(np.float64)
    e = work.flux_err.astype(np.float64)
    sectors = ",".join(str(s) for s in lc.sectors)
    # n_transits_min = 1 makes TLS's own ceiling (n_transits_min / span) the full span, so
    # this rule is the effective P_max; the vetting gate (min_transits = 2) still applies.
    period_max = min(cfg.period_max_fraction_of_span * work.span_days, cfg.period_max_days)
    grid = _grid_kwargs(star, cfg)
    u = limb_darkening(star, cfg)
    windows_json = lc.windows_json()

    edges = segment_edges(work.time, cfg.segment_gap_days)
    signals: list[Signal] = []
    for iteration in range(cfg.max_signals_per_target):
        if len(t) < 100:
            break
        model = transitleastsquares(t, f, e, verbose=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = model.power(
                **grid,
                u=list(u),
                limb_dark="quadratic",
                n_transits_min=cfg.n_transits_min,
                period_min=cfg.period_min_days,
                period_max=period_max,
                duration_grid_step=cfg.duration_grid_step,
                use_threads=use_threads,
                backend=cfg.tls_backend,
                show_progress_bar=False,
                verbose=False,
            )
        sde = _finite(r.SDE, 0.0)
        period = _finite(r.period)
        if sde < cfg.sde_keep or not np.isfinite(period):
            break
        t0 = _finite(r.T0)
        dur_raw = _finite(r.duration)
        t14 = physical_duration(dur_raw, t)
        if not (np.isfinite(t14) and t14 > 0):
            t14 = dur_raw
        depth_frac = 1.0 - _finite(r.depth, 1.0)
        box = white_snr(t, f, period, t0, t14)
        out_period, out_t0, out_depth, snr = period, t0, depth_frac * 1e6, box.snr
        rp_rs, factor = _finite(r.rp_rs), 1
        ref = refine_alias(t, f, period, t0, t14)
        if ref is not None:
            out_period, out_t0, out_depth = ref.period_days, ref.t0_btjd, ref.depth_ppm
            snr, factor = ref.snr, ref.factor
            rp_rs = _rp_rs(ref.depth_ppm * 1e-6, u)
        tt_data = observed_epochs(
            lc.time, out_period, out_t0, t14, min_coverage=cfg.min_epoch_coverage
        )
        signals.append(
            Signal(
                tic_id=tic_id,
                sectors=sectors,
                author=author,
                iteration=iteration,
                period_days=out_period,
                period_err_days=_finite(r.period_uncertainty) * factor,
                t0_btjd=out_t0,
                duration_hours=t14 * 24.0,
                depth_ppm=out_depth,
                sde=sde,
                snr=_finite(snr, 0.0),
                n_transits=len(tt_data),
                alias_factor=factor,
                odd_even_mismatch_sigma=_finite(r.odd_even_mismatch),
                rp_rs=rp_rs,
                fap=_finite(r.FAP),
                detrend_window_days=lc.window_days,
                transit_times_json=json.dumps([round(float(x), 5) for x in tt_data]),
                edge_transit_fraction=edge_fraction(tt_data, edges, cfg.edge_window_days),
                extra={
                    "transit_times": [float(x) for x in tt_data],
                    "duration_raw_hours": dur_raw * 24.0,
                    "snr_pink": pink_snr(t, f, out_period, out_t0, t14),
                    "snr_tls": _finite(r.snr),
                    "detrend_windows_json": windows_json,
                },
            )
        )
        # Mask at the TLS period (a superset of the k*P epochs after refine_alias).
        intransit = transit_mask(t, period, cfg.mask_width_durations * t14, t0)
        t, f, e = t[~intransit], f[~intransit], e[~intransit]
    return signals


# Signal.extra keys that are columns of the `signals` table.
SIGNAL_DB_EXTRAS = ("duration_raw_hours", "snr_pink", "detrend_windows_json")


def signal_row(s: Signal) -> dict:
    """Signal -> dict with the columns of the `signals` table (includes the extras above)."""
    row = s.to_dict()
    for k in SIGNAL_DB_EXTRAS:
        v = s.extra.get(k)
        if isinstance(v, float) and not np.isfinite(v):
            v = None
        row[k] = v
    return row
