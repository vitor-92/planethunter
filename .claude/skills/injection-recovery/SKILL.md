---
name: injection-recovery
description: How to measure pipeline completeness by injecting synthetic transits (batman) into real light curves and how to build the recall benchmark on known TOIs. Use before changing thresholds, detrending or the search algorithm, and to generate training positives for ML.
---

# Injection-recovery and benchmark

## Why

Recall on known TOIs measures the pipeline on what is already known. Injection-recovery measures it in the niches where there are no TOIs (shallow, long-period, faint). Together they define the completeness map.

## Injection

```python
import batman, numpy as np


def inject(t, flux, P, t0, rp_rs, a_rs, inc=90.0, u=(0.4, 0.26)):
    p = batman.TransitParams()
    p.t0, p.per, p.rp, p.a, p.inc = t0, P, rp_rs, a_rs, inc
    p.ecc, p.w, p.limb_dark, p.u = 0.0, 90.0, "quadratic", list(u)
    m = batman.TransitModel(p, t, supersample_factor=7, exp_time=120 / 86400)
    return flux * m.light_curve(p)
```

`a_rs` from the stellar density: `a_rs = ((G*rho*P**2)/(3*pi))**(1/3)`. Impact parameter `b = a_rs*cos(inc)`; draw `b ∈ [0, 0.9]`. Limb darkening coefficients by Teff from the Claret table (or `ldtk`).

Inject into the **raw** flux (before detrending) to also measure the loss caused by detrending.

## Grid

| Axis | Values |
|---|---|
| P (d) | 0.5, 1, 2, 4, 8, 13, 20, 27, 40 |
| Rp (R⊕) | 1, 1.5, 2, 3, 4, 6, 10, 15 |
| b | 0, 0.3, 0.6, 0.9 |
| Target Tmag | 8–10, 10–12, 12–13.5, 13.5–15 |

Pick 200 real light curves with no signal (SDE < 6 in the original search) per Tmag bin. For each cell, ≥ 50 injections with random t0.

## Recovery

Recovered if the period is within 1 % (or alias 2, 1/2) and SDE ≥ threshold. Also store the measured SDE and depth to calibrate bias.

Report: completeness map (P × Rp) per Tmag bin, PNG + CSV, and a marginal recall table with a binomial interval (Wilson, 95 %).

## Benchmark on TOIs

1. Fixed sector (pick a recent one with many TOIs; record the number and the mirror dates).
2. List: TOIs with `tfopwg_disp ∈ {CP, KP, PC}` and ExoFOP SNR > 10 in that sector, with TIC, P, T0, depth.
3. Run ingest → preprocess → search. Recovered = period matches with alias and compatible T0.
4. Metric: total recall and by depth, period and Tmag bin. Target ≥ 90 %.
5. List the missed ones with the likely reason (detrending ate it, low SDE, period outside the grid, quality).

## Before/after

Any PR in `preprocess/`, `search/`, `vetting/` or `crossmatch/` attaches `docs/benchmarks/<date>-<sha>.md` with: recall before/after, Δ per bin, time per sector before/after, list of TOIs that changed status.

## Use for ML

Injections that were recovered and vetted as "pass" = synthetic positives. Unrecovered injections inform the ML limit (there is no point labeling what the search cannot see).

## State in the code (v1)

- Recall benchmark implemented (`benchmark.py`): `planethunter benchmark build N [--kind fp]` and `benchmark run N`. Main metric = recall on TOIs **detectable in one sector** (expected SNR ≥ 7.1 computed from the data, ≥ 2 epochs): the ExoFOP "Planet SNR" is multi-sector.
- The `--kind fp` list (TFOPWG FP/FA) validates vetting by class (`planethunter vet` prints the table).
- Injection-recovery with a P × Rp grid is **not** implemented yet; it is the next step to measure the niches without TOIs.
