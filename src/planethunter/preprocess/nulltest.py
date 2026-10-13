"""Null light curves for the empirical false-alarm rate (Thompson et al. 2018, ApJS 235, 38).

Kepler DR25 ran the full pipeline on inverted and on scrambled light curves: every signal
found there is a false alarm, so the recovered population measures how often systematics and
noise pass the cuts. Pure functions on the ingest DataFrames (columns time, flux, flux_err,
quality, ...); applied before detrending, so the search is exactly the production one.

- inverted: flux -> 2 * median - flux, i.e. 1 - (f - 1) after normalization. Transits become
  bumps (removed by the upper clip); dips from systematics/flares-as-dips remain.
- scrambled: each continuous segment (orbit) is circularly shifted in time by a random 20-80 %
  of its length, all columns except time move together (quality flags travel with the data).
  Real transits keep their spacing inside a segment but lose phase coherence across segments,
  so periodic signals spanning several orbits are destroyed. Limitation: a planet with >= 2
  transits inside one orbit can still be found from that orbit alone. The junction where the
  segment wraps is cut out (a gap wider than the detrending break tolerance) so the detrender
  sees no artificial step.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

NULL_MODES = ("inverted", "scrambled")


def invert_flux(df: pd.DataFrame) -> pd.DataFrame:
    """flux -> 2 * median(flux) - flux (flux_err unchanged)."""
    out = df.copy()
    f = out["flux"].to_numpy(np.float64)
    med = float(np.nanmedian(f[np.isfinite(f) & (f > 0)])) if np.isfinite(f).any() else 1.0
    out["flux"] = (2.0 * med - f).astype(df["flux"].dtype)
    return out


def scramble_segments(
    df: pd.DataFrame, rng: np.random.Generator, *, gap_days: float, cut_days: float
) -> pd.DataFrame:
    """Circularly shift every segment (split at gaps > gap_days) by a random 20-80 % of its
    length; drop +-cut_days/2 around each wrap junction (days)."""
    df = df.sort_values("time", kind="stable").reset_index(drop=True)
    t = df["time"].to_numpy(np.float64)
    cols = [c for c in df.columns if c != "time"]
    breaks = np.flatnonzero(np.diff(t) > gap_days) + 1
    bounds = np.r_[0, breaks, len(t)]
    data = {c: df[c].to_numpy().copy() for c in cols}
    drop = np.zeros(len(t), dtype=bool)
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        n = b - a
        if n < 10:
            continue
        k = int(rng.integers(max(1, int(0.2 * n)), max(2, int(0.8 * n)) + 1))
        for c in cols:
            data[c][a:b] = np.roll(data[c][a:b], k)
        t_junction = 0.5 * (t[a + k - 1] + t[a + k]) if k < n else t[a]
        drop[a:b] |= np.abs(t[a:b] - t_junction) < 0.5 * cut_days
    out = pd.DataFrame({"time": t, **data})[df.columns]
    return out[~drop].reset_index(drop=True)


def apply_null(
    frames: list[tuple[pd.DataFrame, int]],
    mode: str | None,
    *,
    tic_id: int,
    seed: int,
    gap_days: float,
    cut_days: float,
) -> list[tuple[pd.DataFrame, int]]:
    """Transform every sector for a null run. mode None -> unchanged. Deterministic per
    (seed, tic_id, sector)."""
    if mode is None:
        return frames
    if mode not in NULL_MODES:
        raise ValueError(f"unknown null mode {mode!r}; expected one of {NULL_MODES}")
    if mode == "inverted":
        return [(invert_flux(df), s) for df, s in frames]
    return [
        (
            scramble_segments(
                df,
                np.random.default_rng([seed, int(tic_id), int(s)]),
                gap_days=gap_days,
                cut_days=cut_days,
            ),
            s,
        )
        for df, s in frames
    ]
