"""Full search of one target: detrending variants, TLS on each, merge of the signals.

Pure function over DataFrames already loaded. No disk, no network.

Why variants: a long window (1.0 d) preserves long transits but leaves fast variability; a
short window removes variability but eats long transits. Measured in sector 69: TOI 862.01
only shows up with 0.5 d; TOI 190.01 (5.7 h) disappears with 0.3 d. Search both and merge.

Null runs (Thompson et al. 2018) transform the frames before this stage
(preprocess.nulltest.apply_null); the search itself is unchanged.
"""

from __future__ import annotations

import pandas as pd

from planethunter.config import Config
from planethunter.models import Signal, StarParams
from planethunter.preprocess.clean import (
    FlatLightCurve,
    flatten_adaptive,
    flatten_sector,
    red_noise_ratio,
    stitch,
)
from planethunter.search.tls import search_periodic


def detrend_variants(frames: list[tuple[pd.DataFrame, int]], cfg: Config) -> list[FlatLightCurve]:
    """Default variant always; adaptive variant only if some sector has red noise.

    Red noise = robust MAD ratio (red_noise_ratio): a deep transit in white noise no longer
    triggers the adaptive variant. Each variant keeps its per-sector windows.
    """
    default_parts, adaptive_parts, any_red = [], [], False
    pre = cfg.preprocess
    for df, sector in frames:
        base = flatten_sector(df, sector, pre)
        default_parts.append(base)
        ratio = (
            red_noise_ratio(base.flux.astype(float), base.time, bin_hours=pre.red_noise_bin_hours)
            if len(base)
            else float("nan")
        )
        if ratio > pre.red_noise_max:
            any_red = True
            adaptive_parts.append(flatten_adaptive(df, sector, cfg.preprocess, first=base))
        else:
            adaptive_parts.append(base)
    variants = [stitch(default_parts)]
    if any_red:
        variants.append(stitch(adaptive_parts))
    return [v for v in variants if len(v) >= cfg.preprocess.min_points]


def merge_signals(signals: list[Signal], rel_tol: float) -> list[Signal]:
    """Remove duplicates (same period within rel_tol), keeping the one with the highest SDE."""
    kept: list[Signal] = []
    for s in sorted(signals, key=lambda x: -x.sde):
        if all(abs(s.period_days / k.period_days - 1) > rel_tol for k in kept):
            kept.append(s)
    for i, s in enumerate(kept):
        s.iteration = i
    return kept


def search_target(
    frames: list[tuple[pd.DataFrame, int]],
    star: StarParams | None,
    cfg: Config,
    *,
    tic_id: int,
    author: str = "SPOC",
) -> list[Signal]:
    """All detrending variants of one target -> merged signals (see search_periodic)."""
    found: list[Signal] = []
    for lc in detrend_variants(frames, cfg):
        found += search_periodic(lc, star, cfg.search, tic_id=tic_id, author=author)
    return merge_signals(found, cfg.crossmatch.period_rel_tol)
