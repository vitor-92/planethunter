# M3. Periodograms: how a period is found

<p class="meta">Intermediate level · weeks 5–6 · about 10 hours</p>

!!! abstract "In this lesson you will learn"
    - The idea behind BLS (Box Least Squares) and what TLS changes.
    - What SDE is and why the limit is 9.
    - How the period grid is built, and why its limits changed the recall.
    - Why aliases (P/2, 2P, P/3) show up and how PlanetHunter fixes the P/3 case.
    - How the iterative search with masking works.
    - Why the detrending window decides what you are able to find, with measured numbers.
    - The effect of gaps and segment edges in TESS data.

## The problem

You have 27 days of brightness measured every 2 minutes, about 18,000 points. Somewhere in there are 300 ppm dips, with a noise of 130 ppm per point. You do not know the period, when the first transit happened, or how long each one lasts.

The solution is organized brute force: **test every combination** and measure which one best explains the data. The plot of "how well each period explains the data" is the **periodogram**.

## BLS: looking for boxes

**BLS** (*Box Least Squares*, Kovács, Zucker & Mazeh, 2002) models the transit as a **box**: constant brightness outside, constant and lower brightness inside.

For each period $P$ in the grid:

1. **Fold** the curve: compute the phase of each point, the remainder of dividing the time by $P$. If $P$ is right, all the transits land on top of each other.
2. For each **position** of the box in phase and each **duration** in the grid, compare the mean of the points inside the box with the mean outside.
3. Compute how much the box model reduces the squared error compared with a straight line. That reduction is the BLS **power** at that period.

For each period, the periodogram keeps the best power among all positions and durations. The highest peak is the candidate period.

Analogy: it is like looking for a beat in a noisy recording. You try several rhythms and, for each one, you stack the measures on top of each other. At the right rhythm, the beats add up and stand out; at the wrong ones, they spread out.

## TLS: looking for real transits

**TLS** (*Transit Least Squares*, Hippke & Heller, 2019) does the same search, but swaps the box for a **realistic transit model**: entry and exit ramps, and a bottom rounded by limb darkening (lesson [M2](m2-transit-physics.md)). The model is tailored to the star: PlanetHunter passes in the radius and mass from the TIC.

Why does this help? The box gets the ramps and the bottom wrong. For strong transits, it makes no difference. For **small** planets, close to the detection limit, that error eats part of the signal. The realistic model recovers that part, and the authors show a gain in sensitivity precisely for small planets. In exchange, TLS is slower.

PlanetHunter uses TLS 2.0 (backend `fused-pl`, one thread per target, in parallel across stars).

## SDE: does the peak stand out?

For each period, TLS computes a goodness-of-fit value (called SR). The **SDE** (*Signal Detection Efficiency*) measures how much the highest peak stands out from the rest:

$$
\text{SDE} = \frac{\text{SR}_\text{peak} - \overline{\text{SR}}}{\sigma_\text{SR}}
$$

It is the number of standard deviations by which the peak sits above the mean of the periodogram. A high SDE says: "this period is much better than all the others".

**Why 9?** Hippke & Heller (2019) simulated curves with white noise only and measured how often the highest peak went past each SDE: SDE 7 gives a false alarm probability (FAP) of about 1 %. The TLS documentation repeats the test with more curves: SDE 9.1 gives about $10^{-4}$, 1 in 10,000 pure-noise curves. This is the `sde_min: 9.0` in `config/thresholds.yaml`. Real light curves also have red noise, so the true false alarm rate is higher than these numbers.

The system also keeps signals with SDE between 7 and 9 (`sde_keep: 7.0`), but they do not become candidates. They serve as weak examples for the future machine learning classifier.

!!! note "SDE and SNR measure different things"
    The SDE compares the peak with the **rest of the periodogram**: "does this period stand out?". The SNR compares the depth with the **noise of the curve**: "is the dip large?" (lesson [M1](m1-statistics-for-signals.md)). A signal can have a high SDE and a low SNR, or the other way around. PlanetHunter requires both: SDE ≥ 9 **and** SNR ≥ 7.1.

## The period grid

TLS does not test infinitely many periods. It tests a **grid**, and the grid decides what can be found. The project's parameters:

| Parameter | Value | Why |
|---|---|---|
| `period_min_days` | 0.2 d | Absolute floor of the grid |
| `roche_min_a_rstar` | 2.0 | The shortest period tested is the one where the orbit is 2 stellar radii from the star's center, as in the TESS quick-look pipeline (QLP); about 0.2 to 0.3 d for a Sun-like star |
| `period_max_fraction_of_span` | 0.9 × length of the data | Two transits are enough to define a period |
| `period_max_days` | 40 d | Absolute ceiling (see below) |
| `oversampling_factor` | 3 | Grid density; higher = slower and finer |
| `duration_grid_step` | 1.1 | Each duration tested is 10% longer than the previous one |
| `bin_minutes` | 10 | Groups 2-min points into 10-min bins to speed things up; loses little for P > 1 d |
| `limb_darkening` | `tess` | The transit model uses limb darkening for the TESS band, chosen from the star's temperature and surface gravity |

Each of these numbers has a story measured in the sector 69 benchmark:

- **Stellar limits.** At first, the duration grid only accepted stars within ±30% of the TIC radius and mass. Transits shorter than the central one (high b, wrong TIC radius) were left out. TOI 196.01, 347.01, 386.01 and 2339.01 went missing; with wide limits, they show up with SDE from 8.6 to 16.8.
- **Minimum period and the Roche limit.** TLS computes the shortest possible period from the model's radius (a planet cannot orbit inside the star). With the TIC radius of 4.06 R☉, the grid started at 4.15 d, and TOI 196.01, with P = 1.16 d, went missing. Fix: the model uses at most 1.5 R☉ and 1.5 M☉. A later audit (2026-10-10) found a second limit: TLS assumes an orbit of at least 3 stellar radii, so the shortest period tested was really 0.6 to 1.0 d, and 13 of 505 sector 69 TOIs were outside the grid. Today the minimum is 2 stellar radii (as in QLP), with a floor of 0.2 d.
- **The real maximum period.** TLS, by default, only tests periods with room for 2 transits, so the real ceiling was half the data span and `period_max_fraction_of_span` did nothing. The project now lets TLS go up to the span and applies the 0.9 limit itself; the vetting still requires 2 transits.
- **40-day ceiling.** In the search with several sectors separated by years (data covering ~800 days), the grid became huge and produced spurious aliases of 26 to 64 days with 1 or 2 transits.

Combined result of the changes up to 2026-10-09: recall went from 84.4% to 91.1% on detectable TOIs. The 2026-10-10 changes still need a new measurement.

### What PlanetHunter measures after TLS

TLS gives the period, the transit time, the depth and the SDE. Four other numbers are measured again by the project, because every later step depends on them:

- **Duration (T14).** TLS multiplies the duration by the fraction of time that has data (the fill factor). For one sector it is a little below 1 (0.86 in sector 69), so durations came out about 15% short. With two sectors years apart it is tiny: a 3 h transit came out as 0.23 h. The project divides by the fill factor and stores the physical T14.
- **SNR.** Measured on the flattened curve, with points within half a T14 of the transit center counted as "in transit" and a robust noise (MAD) from the points outside.
- **S/N_pink.** The SNR with red noise included (lesson [M1](m1-statistics-for-signals.md)), stored for vetting.
- **Number of transits.** An epoch counts only if at least 50% of its expected transit time has data. A transit mostly lost in a gap no longer counts.

The audit found why this matters: the shrunken T14 was being used everywhere afterwards (the SNR, the masking in the iterative search, the windows of the vetting tests), so one error spread through the whole pipeline.

## Aliases: the ghost peaks

An **alias** is a wrong period that is a simple multiple or fraction of the true one. Why do they show up?

- **At 2P**, you fold the curve with twice the period. Half of the transits land at phase 0 and the other half at phase 0.5. The box at phase 0 still catches real transits, with half of the points. A lower peak, but a peak.
- **At P/2**, each predicted "transit" alternates between a real one and an empty one. The mean depth drops by half.
- **At P/3, 3P/2, 2P/3**, the same logic, with different fractions.

Example measured in lesson [M4](m4-tess-data-in-python.md), with Lightkurve's BLS on Pi Men c (sector 1): main peak at 6.27 d with power 1,400; smaller peaks at 12.53 d (2P, power 857), 3.13 d (P/2, power 746), plus 9.4 d (3P/2) and 2.09 d (P/3). At the P/2 period, the computed depth drops from 228 to 126 ppm: about half, as the explanation predicts.

!!! warning "Binary with period 2P"
    An eclipsing binary with two similar stars has two eclipses per orbit. The search finds the period P between consecutive eclipses, which is **half** of the true orbital period. That is why the `odd_even` test compares odd and even transits: if the stars are a little different, alternating eclipses will have different depths.

### The P/3 case and `refine_alias`

With few transits and gaps in the data, TLS sometimes prefers one third of the true period. Imagine a 12.6 d planet in a 27 d sector: two transits. At P/3 = 4.2 d, TLS predicts six transits. Two are real; the other four fall into gaps or get diluted in the average. The peak at P/3 can win.

That is exactly what happened in sector 69: **TOI 899.01, 924.01 and 3262.01** (periods of 12 to 13 days) came out at about 4.2 d.

The fix, the `refine_alias` function in `search/tls.py`, runs a direct test for k = 3 and k = 2:

1. It splits the epochs predicted by P into two groups: **A**, those that would also be predicted by kP, and **B**, those that exist only under P.
2. It measures the depth in each group.
3. It accepts kP if group A shows a transit (more than 3 sigma), group B **has data** but shows no transit (less than 3 sigma), and the depth of A is more than 3 times that of B.

In words: if the "extra" transits predicted by P fall on good data and do not show up, the true period is the longer one. The SNR is then measured again with the transits of the true period only (before, it stayed too low by a factor of up to 0.58). The dossier shows the result in the "Applied alias factor" field.

## Iterative search with masking

A star can have more than one planet. TLS only returns the strongest peak. The solution:

1. Search and find the strongest signal.
2. **Erase** (mask) the points of its transits, in a window of 2 durations (`mask_width_durations: 2.0`, using the physical T14).
3. Search again in the remaining curve.
4. Repeat up to 3 times (`max_signals_per_target: 3`) or until the SDE drops below 7.

For Pi Men c, after masking the 5 transits, the second BLS search finds nothing relevant (best peak at 37 ppm and low prominence). That is what you would expect: in sector 1, only Pi Men c transits.

!!! tip "In the tool"
    The search lives in `search_periodic` (`src/planethunter/search/tls.py`). Each signal comes out with `iteration` (0, 1, 2), `sde`, `snr`, `n_transits`, `alias_factor` and the detrending window used. In vetting, the `independence` test checks whether a signal survives when the stronger signals of the same star are masked: in sector 69, signal 1601 (11.95 d) was reusing the eclipses of signal 1600 (6.75 d) and was vetoed.

## Detrending: the window that decides

Before the search, the curve needs to be **flattened**: the star's slow variation (rotation, spots) is removed to leave the transits visible. PlanetHunter uses the **biweight** filter from the wotan library: for each point, it estimates the local trend in a window of fixed width, robustly (it ignores outlying points such as those in the transit), and divides the curve by it.

The dilemma: if the window is **short**, the filter also follows the transit and "eats" it. If it is **long**, it leaves the star's fast variability behind.

Measured by the project with a synthetic 1,500 ppm box transit, with no variability:

| Window | 3 h transit | 5 h transit |
|---|---|---|
| 0.5 d | loses 8% of the depth | loses **40%** |
| 1.0 d | loses 0% | loses 6% |

The rule of thumb is a window about 3 times the duration of the longest transit you are looking for. The default is **1.0 d** (`window_length_days`). Transits of 5 to 6 h show up at periods of 20 to 40 d on a star like the Sun (lesson M2) or at shorter periods on larger stars.

### Detrending variants

A single window does not suit every star. The system measures the leftover variability after flattening through the ratio between the spread of the curve and the point-to-point noise, both measured with the MAD (lesson M1). The MAD matters: with the standard deviation, a deep transit inflated the ratio by itself and pushed the system toward short windows, the ones that eat transits. If it goes past 1.2 (`red_noise_max`), it redoes the detrending with windows of 0.5 d and then 0.3 d (`fallback_windows_days`). And it searches **both** versions, default and adaptive, merging the signals (the one with the higher SDE wins when two have the same period).

Why both? Two real cases from sector 69:

- **TOI 862.01** (5,092 ppm): the star varies quickly. With a 1.0 d window, the noise ratio stayed well above 1.2 and the signal disappeared. With 0.5 d, it shows up with SDE 18.
- **TOI 190.01** (5.7 h transit): with a 0.3 d window, the depth of 8,248 ppm turned into 347 ppm. The short window ate the transit.

The short window alone loses the second one; the long window alone loses the first. Searching both and merging saved both.

### Flattening again for vetting

Once a signal is found, its duration and transit times are known. The vetting then flattens each sector again, with that sector's own window from the search but never shorter than 3 times T14, and with the transits **masked**: the filter does not see them, and it draws the trend across them (Hippke et al. 2019). Measured with a 12 h transit: a plain 1.0 d window keeps 50% of the depth; this masked flattening keeps 99%. The same curve feeds the vetting tests, the FPP and the dossier.

Two more precautions during cleaning: remove outlying points **only upward** (`sigma_upper: 4.0`), never downward; and do not cut the segment edges (`edge_cutoff_days: 0.0`), to preserve single events near them.

!!! example "Exercise 1"
    A candidate has 5-hour transits and a true depth of 1,500 ppm. What depth do you expect to measure with a 0.5 d window? And with 1.0 d? If the noise gives SNR 10 at the true depth, would the signal pass the SNR limit with the 0.5 d window?

    ??? success "Show answer"
        With 0.5 d, it loses 40%: you measure about 1,500 × 0.6 = **900 ppm**. With 1.0 d, it loses 6%: about **1,410 ppm**.

        The SNR is proportional to the depth. With 0.5 d: 10 × 0.6 = **6.0**, below 7.1. The `snr` gate would veto the signal. With 1.0 d: 10 × 0.94 = 9.4, it passes. The choice of window, on its own, decides whether this planet is found.

## Gaps and segment edges

TESS data are not continuous. A sector of ~27 days has a **gap** in the middle to send data to Earth, and sometimes others because of problems. Each continuous stretch is a **segment**.

Gaps get in the way in three ways:

1. **Lost transits.** A transit that falls in the gap does not exist in the data. With a long period, this can leave a single transit, and the signal is vetoed by `n_transits`.
2. **Aliases.** The gap is what makes the P/3 case possible: the "extra" transits fall into it and nothing contradicts the short period.
3. **Edges.** At the ends of each segment, the detrending has data on one side only and can create artificial **ramps**. The project measured this: pure noise, with 2,000 ppm of variability, produced SDE ~10 at a period equal to one TESS orbit, with the "event" 0.07 d from the edge.

That is why each signal comes out with `edge_transit_fraction`: the fraction of transits with data whose center is less than 0.5 d (`edge_window_days`) from a segment edge. Signals with more than 50% of their transits at edges (`max_edge_transit_fraction: 0.5`) do not become candidates, and the `edges_dumps` vetting test fails by the same criterion (or if more than 50% fall near a pointing adjustment, the *momentum dump*).

!!! example "Exercise 2"
    Pi Men c in sector 1 had 5 transits, at BTJD 1325.50, 1331.77, 1338.04, 1344.31 and 1350.57. The data start at 1325.30, end at 1353.18, and there is a gap between 1338.52 and 1339.66. Compute `edge_transit_fraction`. Would the signal be blocked?

    ??? success "Show answer"
        Distance from each transit to the nearest edge:

        - 1325.50: 0.20 d from the start (1325.30). **At an edge.**
        - 1331.77: far from any edge.
        - 1338.04: about 0.48 d from the start of the gap (1338.52). **At an edge.**
        - 1344.31 and 1350.57: far from the edges (the end of the data is at 1353.18).

        That is 2 of 5: **edge_transit_fraction = 0.4**. This is exactly the value PlanetHunter computes for this signal. Since 0.4 ≤ 0.5, the signal is **not** blocked, and the `edges_dumps` test passes.

!!! tip "In the tool"
    In the dossier, the **"Light curve"** section shows the transits as red lines and the telescope adjustments as dotted blue lines. Transits stuck to a segment edge or to a blue line are a warning sign. The note of the `edges_dumps` test gives both fractions: "at momentum dump X%, at segment edge Y%". The **Provenance** section shows the detrending window used.

## Lesson checklist

- [ ] I can explain BLS in three steps (fold, test boxes, measure the improvement).
- [ ] I know what TLS changes and why that helps small planets.
- [ ] I can define SDE and say where the limit of 9 comes from.
- [ ] I can explain why peaks show up at 2P and P/2, and what `refine_alias` does with P/3.
- [ ] I can describe the iterative search and the `independence` test.
- [ ] I can explain the detrending window dilemma with the measured numbers (40% and 6%).
- [ ] I can compute `edge_transit_fraction` for a list of transits.
- [ ] I found the alias factor and the detrending window in a dossier.

## Going further

- Astropy documentation on Box Least Squares ([docs.astropy.org](https://docs.astropy.org/en/stable/timeseries/bls.html)): short BLS examples in Python.
- Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39 (TLS), also on arXiv ([arXiv:1901.02015](https://arxiv.org/abs/1901.02015)). Read the introduction and the figures; the comparison with BLS and the SDE calibration are there.
- Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. The original BLS paper. It is left for the advanced level ([A1](../advanced/a1-detection-algorithms.md)), but the first figure alone is worth the visit.
- Hippke et al. (2019), *The Astronomical Journal* 158, 143: the wotan paper, with the comparison of detrending filters.
- In the repository, `docs/benchmarks/2026-10-09-s0069-history.md`: the table "Causes found and fixed" is this lesson summarized as a diagnosis.
