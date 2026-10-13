---
name: transit-search
description: Parameters and reference code for detrending (wotan), periodic search (TLS/BLS), iterative search with masking, single-transit detection and SDE/SNR thresholds. Use when implementing or tuning the transit search stage.
---

# Transit search

## Detrending (wotan)

```python
from wotan import flatten

flat, trend = flatten(
    t,
    f,
    method="biweight",
    window_length=0.5,
    edge_cutoff=0.5,
    break_tolerance=0.5,
    return_trend=True,
)
```

- `window_length` = 3 × maximum expected duration. Measured in the project: 0.5 d loses 8 % of the depth on a 3 h transit and 40 % on a 5 h one; 1.0 d loses 0 % and 6 %. Project default: 1.0 d. For single transits, 1.5–2.0 d.
- Segment edges: detrending ramps mimic transits (measured: noise + 2000 ppm variability gave SDE ~10 at P = 1 orbit). Every signal records `edge_transit_fraction`; candidates require ≤ 0.5.
- `break_tolerance=0.5` splits at orbit gaps.
- Validate: inject a 12 h transit and confirm that ≥ 90 % of the depth survives.

## TLS

```python
from transitleastsquares import transitleastsquares

model = transitleastsquares(t, flat)
r = model.power(
    R_star=min(rs, 1.5) * 2 / 3,  # TLS f_max uses a = 3 R*; x 2/3 gives a = 2 R* (QLP)
    M_star=min(ms, 1.5),
    R_star_min=0.13,  # duration grid always wide (wrong TIC radii, high b)
    R_star_max=max(3.5, 1.3 * rs),
    M_star_min=0.1,
    M_star_max=max(2.0, 1.3 * ms),
    oversampling_factor=2,  # 3 x 2/3: same Ofir density as R* unscaled
    n_transits_min=1,  # else TLS caps P at span / 2
    period_min=0.2,
    period_max=min(0.9 * (t.max() - t.min()), 40.0),
    duration_grid_step=1.1,
    u=[u1, u2],  # Claret TESS band (ld_claret_tess.csv in the TLS package)
    use_threads=1,  # parallelize per target
    show_progress_bar=False,
)
depth_ppm = (1 - r.depth) * 1e6  # r.depth is in-transit flux, e.g. 0.995
# TLS 2.0 multiplies T14 by the fill factor of the series (fraction of cadences present over
# the whole span): 0.96 for one sector, ~0.07 for two sectors 700 d apart. Undo it.
t14 = r.duration / fill_factor(t)  # search/stats.py::physical_duration
```

Do NOT use `r.duration`, `r.snr`, `r.distinct_transit_count` or `r.snr_pink_per_transit` as they
are: all are computed with the shrunken duration. Recompute with T14 (`search/stats.py`).

Thresholds: Hippke & Heller 2019 calibrate SDE 7 ≈ FAP 1 %; the TLS documentation gives SDE 9.1 ≈ FAP 1e-4. Both are for white noise; with red noise the real false-alarm rate is higher (see docs/LITERATURE.md). Use SDE ≥ 9 and SNR ≥ 7.1 as the candidate cut; keep everything with SDE ≥ 7 for ML.

## BLS (fast fallback)

```python
import numpy as np
from astropy.timeseries import BoxLeastSquares

bls = BoxLeastSquares(t, flat, dy=e)
periods = np.exp(np.linspace(np.log(0.5), np.log(pmax), 50_000))
res = bls.power(periods, durations=[0.04, 0.08, 0.15, 0.25], objective="snr")
```

## Iterative search

After finding a signal, mask `|phase| < T14` (`mask_width_durations = 2`) with TLS
`transit_mask`, rerun. With the shrunken TLS duration the mask was too narrow and the same
signal filled all 3 slots in multi-sector runs. Stop at SDE < 7 or 3 signals. Essential for extra planets in known systems.

## Single transit

1. Trapezoidal templates with durations of 1–24 h, unit depth.
2. Sliding correlation on the light curve detrended with a long window (1–2 d); local SNR = fitted depth / local σ.
3. Candidate if SNR ≥ 8, outside ±0.3 d of orbit edges and momentum dumps, and with no second event compatible with P < span.
4. Lower period limit for b = 0:

```python
import astropy.units as u, astropy.constants as c, numpy as np

P_min = (np.pi * c.G * M_star * T_dur**3 / (4 * R_star**3)).to(u.day)
```

5. Look for a second event in other sectors of the same target (duo-transit): allowed periods = Δt / n for integer n, filtered to those that have no transit in the observed gaps.

## Multi-sector

Normalize each sector by its median, concatenate, detrend per sector, TLS with `period_max` up to half the total span. Shallow signals require ≥ 10 sectors; TLS cost grows with span, use `oversampling_factor=2`.

## Performance

TLS is O(N_periods × N_durations × N_points). One 2-min target over 1 sector (~18k points): 20–60 s on 1 core. 20k targets on 8 cores ≈ 1.5–4 h. Options: binning to 10 min before TLS (loses little for P > 1 d), BLS first as a pre-filter, GPU with `cuvarbase` for BLS.

## State in the code (v2, audit 2026-10-10)

- `search/target.py::search_target`: detrending in two variants (1.0 d window always; smaller 0.5/0.3 d window only if the red-noise ratio > 1.2) and TLS on each; signals merged without duplicates. The red-noise ratio is MAD(flux) / point-to-point MAD (`preprocess/clean.py::red_noise_ratio`): a deep transit in white noise gives ~1 (the old std/p2p gave > 3 and selected windows that ate the transit). On 300 sector 69 targets: 16.0 % flagged vs 18.7 % with std (all 8 stars dropped have deep dips, 5 are TOIs). A Pont (2006) beta on 1 h bins is available (`red_noise_bin_hours`) but flags 41 %.
- Per-sector windows: `FlatLightCurve.windows` -> `signals.detrend_windows_json` (`{"sector": window_days}`). `signals.detrend_window_days` is still the smallest one.
- `search/tls.py::search_periodic`: TLS 2.0, `fused-pl` backend, **1 thread per target** (8 threads on Windows: 18.7 s vs 0.7 s due to process overhead; parallelize per target with `ProcessPoolExecutor`, always with an `if __name__ == "__main__"` guard).
- What comes from TLS: period, T0, depth, SDE, FAP, odd/even. What is recomputed (`search/stats.py`):
  - `duration_hours` = T14 = `r.duration / fill_factor` (`duration_raw_hours` keeps the TLS value);
  - `snr` = in-transit mean over ±T14/2 vs 1.4826·MAD out of transit (|phase| > T14), ×√N_in; after `refine_alias` it is measured on the k·P epochs only (was √(n_A/n) low);
  - `snr_pink` = Pont 2006 S/N on the T14 scale (σ_w from MAD, σ_r from T14 bins), stored, **not gated yet** (QLP uses S/N_pink > 9);
  - `n_transits` = epochs with ≥ 50 % of [−T14/2, +T14/2] covered (`min_epoch_coverage`).
- Period grid: `n_transits_min = 1` (TLS's own ceiling becomes the span, so `period_max = min(0.9 × span, 40 d)` is effective); P_min from a = 2 R* (QLP) by passing R* × 2/3 and oversampling × 2/3 (same Ofir density), floor `period_min_days = 0.2`. Grid star capped at R, M ≤ 1.5 (with R = 4 from the TIC the grid started at 4.15 d). Duration grid limits always wide (R 0.13–3.5, M 0.1–2.0).
- TLS 2.0 template is fixed (per/rp/a/inc defaults); R*/M* only drive the grids. `u` does change it: `limb_darkening: tess` takes Claret TESS-band (u1, u2) from Teff/logg in TLS's bundled `ld_claret_tess.csv`.
- `refine_alias`: tests 2P and 3P when extra epochs of P have data without a transit (P/3 with 2 transits and gaps); returns the SNR of the true period; `rp_rs` is recomputed from its depth.
- Each signal records `edge_transit_fraction` (detrending ramps at orbit edges mimic transits) and `transit_times_json` (observed epochs only).
- Vetting re-detrend (`preprocess/clean.py::signal_windows`, `flatten_for_signal`): each sector with its own search-time window, never below 3 × T14, with the signal's transits **and phase 0.5** masked over 1.5 × T14 (wotan mask). 12 h transit: plain 1.0 d window keeps 50 %, masked re-detrend keeps 99 %.
- `flux_err` is divided by the trend after detrending.
- Null runs (Thompson et al. 2018): `planethunter search --null inverted|scrambled` (`preprocess/nulltest.py`); `search_runs.mode = "null-inverted" | "null-scrambled"`; vetting re-applies the same transform. Scrambling circularly shifts each orbit, so a planet with ≥ 2 transits per orbit survives inside that orbit; inverted strong transits can leave dips on their flanks after detrending.
- `search/gpu_bls.py` (pre-filter, optional): Ofir f^(1/3) grid, same P range as TLS, phase bins so the shortest duration spans ≥ 2 bins.
- Red-noise residuals (e.g. a 2000 ppm, 5 d sinusoid after the 1.0 d biweight) produce real periodic dips with SDE 8–10 that SDE/SNR cannot reject; S/N_pink stays < 9 for them.
- Benchmark before these changes: 91.1 % recall on the detectable TOIs of sector 69 (`planethunter benchmark run 69`); rerun pending.
