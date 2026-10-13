# A1. Detection algorithms in depth

<p class="meta">Advanced level · weeks 1–3 · about 14 hours</p>

!!! abstract "In this lesson you will learn"
    - The statistics behind BLS (Kovács, Zucker & Mazeh 2002) and why, deep down, it is a signal-to-noise ratio.
    - What TLS (Hippke & Heller 2019) changes compared with BLS and how much that costs.
    - The trade-offs between three ways of detrending: biweight, spline and Gaussian processes.
    - Why single transits and double transits are the niche with the most planets left to find, and why they are hard.
    - The current limits of PlanetHunter's search and where they came from.

In [lesson M3](../intermediate/m3-periodograms.md) you saw the idea of the periodogram. Now the question is: **what exactly is being maximized, and why?**

## 1. The search as a grid of hypothesis tests

Every search for periodic transits tests three parameters: **period** $P$ (days), **epoch** $T_0$ (the time of one transit, in BTJD) and **duration** $T_{14}$ (hours). For each trio, the algorithm compares "constant brightness" with "constant brightness, except during transits that repeat every $P$". The periodogram shows, for each $P$, the improvement obtained with the best $T_0$ and the best duration.

An important consequence: there are **millions of tests**, and noise alone produces peaks. With a million tries, some 3-sigma peak shows up by chance almost for sure. This is the **look-elsewhere effect**, which comes back in lesson A5, in the noise floor the project measured.

## 2. BLS: the statistics behind it

**BLS** (Box Least Squares) was published by Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. The model is a box: brightness $H$ outside the transit, brightness $L$ inside, with an instant transition.

### The definitions in the paper

The data are $N$ flux measurements $x_i$ with errors $\sigma_i$. First, the weighted mean is subtracted, so the data are centered on zero. Each point gets a normalized weight:

$$
w_i = \frac{\sigma_i^{-2}}{\sum_j \sigma_j^{-2}}, \qquad \sum_i w_i = 1 .
$$

For a trial period, the points are phase-folded. You pick a phase interval as the candidate transit and define:

$$
r = \sum_{i \in \text{transit}} w_i, \qquad s = \sum_{i \in \text{transit}} w_i \, x_i .
$$

In words: $r$ is the **fraction of the weight** that falls inside the transit (if all errors are equal, it is simply the fraction of points) and $s$ is the **weighted sum of the flux** inside the transit. If there is a dip, $s$ is negative.

The paper shows that the sum of squared residuals of the best box model is

$$
D = \sum_i w_i x_i^2 - \frac{s^2}{r(1-r)} .
$$

The first term does not depend on the model. So **minimizing $D$ is the same as maximizing $s^2/[r(1-r)]$**. BLS computes this quantity for every interval and keeps the largest value. Its square root is the **SR** (signal residue) for that period:

$$
\text{SR} = \max \left[ \frac{s^2}{r(1-r)} \right]^{1/2} .
$$

The depth of the best model comes for free: $\delta = H - L = |s| / [r(1-r)]$.

### Why this is a signal-to-noise ratio

Assume equal errors, $\sigma_i = \sigma$, and a transit of depth $\delta$ covering a fraction $r$ of the points. With the data centered on zero, the level inside is $L = -\delta(1-r)$ and outside it is $H = \delta r$. Then $s = rL = -\delta\, r(1-r)$ and

$$
\frac{s^2}{r(1-r)} = \delta^2\, r(1-r) .
$$

Multiplying by $N/\sigma^2$ (to go back from normalized weights to chi-squared), the improvement in the fit is

$$
\Delta\chi^2 = \frac{N \, \delta^2 \, r(1-r)}{\sigma^2}
\quad \Longrightarrow \quad
\sqrt{\Delta\chi^2} = \frac{\delta}{\sigma}\sqrt{N r (1-r)} \approx \frac{\delta}{\sigma}\sqrt{N_\text{in transit}} .
$$

This is the SNR formula from the intermediate level: depth over the noise of one point, times the square root of the number of points in transit. BLS looks for the period that **maximizes the SNR of a box**. And what you saw in [lesson M1](../intermediate/m1-statistics-for-signals.md) still holds: with correlated noise, $\sigma/\sqrt{N}$ underestimates the error and BLS becomes optimistic.

### SDE: does the peak stand out?

SR on its own depends on the scale of the data. To compare stars, Kovács et al. define the **SDE** (Signal Detection Efficiency):

$$
\text{SDE} = \frac{\text{SR}_\text{peak} - \langle \text{SR} \rangle}{\text{standard deviation}(\text{SR})} .
$$

In words: how many standard deviations the peak sits above the mean of the periodogram. Because it is **relative to the periodogram itself**, it can be compared between stars of different brightness.

## 3. TLS: what changes

**TLS** (Transit Least Squares), by Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39, is the algorithm PlanetHunter uses. The central idea is simple: **a real transit is not a box**. It has a gradual entry and exit (ingress and egress) and a rounded bottom because of limb darkening (the edge of the star is darker than its center, as you saw in [lesson M2](../intermediate/m2-transit-physics.md)).

### The main differences

| Aspect | BLS | TLS |
|---|---|---|
| Model | Two-level box | Transit with limb darkening (in PlanetHunter, TESS-band coefficients chosen from the star's temperature and gravity) |
| Fit measure | $s^2/[r(1-r)]$ | Chi-squared of the model fit |
| Spectrum | SR(P) | $\text{SR}(P) = \chi^2_\text{min, global} / \chi^2_\text{min}(P)$, between 0 and 1 |
| SDE | (peak − mean) / deviation | $(1 - \langle\text{SR}\rangle)/\sigma_\text{SR}$, with the trend of the spectrum removed |
| Period grid | Free | Optimal sampling in frequency (Ofir 2014) |
| Duration grid | Free | Limited by physics: the star's radius and mass fix the possible duration for each period |
| Cost | Low | Much higher; needs parallelism |

The gain comes from two sources. The realistic model matches the signal better, especially for small planets, where ingress and egress are a large fraction of the transit; the authors show a higher SDE than BLS on the same data. And the duration grid limited by the star avoids testing impossible durations, which cuts the number of tries and the spurious peaks.

The **SDE ≥ 9** limit comes from the TLS paper: with white noise, it corresponds to a false alarm probability of the order of $10^{-4}$ (`sde_min` in `config/thresholds.yaml`).

### What not to take from TLS as is

Two TLS outputs were silently wrong for the project's use, and the 2026-10-10 code audit found both:

- **Duration.** TLS 2.0 multiplies the transit duration by the fill factor of the series (the fraction of cadences present over the whole span). For one sector that is a little below 1 (0.86 in sector 69). For two sectors 700 days apart it is about 0.07, and a 3 h transit came out as 0.23 h. Since the same duration fed the SNR, the iterative masking and the vetting windows, the error spread through the whole pipeline. The project now divides it back (`search/stats.py`) and keeps the TLS value only as `duration_raw_hours`.
- **SNR and S/N_pink.** The SNR is recomputed on the flattened curve with the physical T14 and a robust noise. TLS already computes a per-transit S/N_pink (Pont et al. 2006), which was being discarded; it is now combined, $\sqrt{\sum_i \text{S/N}_{\text{pink},i}^2}$, and stored at no extra CPU cost. The vetting uses it with the QLP threshold of 9.

The general rule: before trusting a number from a library, check its definition against the paper and against a known case.

### Measuring the false alarm rate: null runs

The SDE threshold assumes white noise; real light curves are not white. Kepler measured the false alarm rate directly (Thompson et al. 2018): it searched light curves that **cannot** contain real transits and counted what came out. PlanetHunter does the same with `planethunter search --null inverted` (the flux is turned upside down, so dips become bumps) and `--null scrambled` (each orbit of data is shifted in time, so transits no longer line up across orbits). Every signal from these runs is a false alarm by construction. They serve two purposes: to estimate how many of the `NEW` signals are expected to be noise, and to give the machine-learning model realistic negatives (lesson A4). The cost is one extra search per null mode.

### The price of physics: stellar limits

The duration grid depends on the star's radius and mass, and the project got burned by this twice (benchmark history):

- **Limits too narrow.** With radius and mass limited to ±30 % of the TIC value, transits shorter than predicted (high impact parameter) fell outside the grid. TOI 196.01, 347.01, 386.01 and 2339.01 only showed up with wide limits (SDE 8.6 to 16.8).
- **Stellar radius in the minimum period.** TLS derives the shortest period from the Roche limit, which depends on the radius. With $R = 4.06\,R_\odot$ in the TIC, the grid started at 4.15 days, and TOI 196.01 has 1.16 days. Fix: a model with radius and mass capped at 1.5.
- **Three stellar radii.** TLS places the shortest orbit at 3 stellar radii, which put the real minimum period at 0.6 to 1.0 days: 13 of 505 sector 69 TOIs were outside the grid. The project now uses 2 stellar radii, as QLP does (Kunimoto et al. 2023), with a floor of 0.2 days.

Lesson learned: every piece of "physical" information given to the algorithm is also an assumption that may be wrong.

## 4. Detrending: biweight, spline and GP

Before searching, you need to remove the star's slow variation (rotation, spots, telescope systematics). The choice of method decides what survives.

| Method | How it works | Advantage | Risk |
|---|---|---|---|
| Sliding-window **biweight** | For each point, estimates the "typical level" of its neighbors within a time window, giving little weight to points far from the median | Robust to transits and outliers; a single parameter (the window); fast | A short window eats long transits; a long window leaves fast variability |
| Robust **spline** | A smooth curve made of piecewise polynomials, fitted several times while discarding outlying points | Good for slow, smooth trends | The spacing of the knots plays the role of the window; can wiggle near gaps |
| **Gaussian process** (GP) | A statistical model of correlated noise, with a "kernel" that describes how similar nearby points are (for example, quasi-periodic for rotation) | Follows the complex variability of young, active stars; gives an uncertainty | Too flexible: absorbs the transit if it is not masked; expensive; you must choose the kernel |

The wotan paper (Hippke et al. 2019, *AJ* 158, 143), the library the project uses, compared dozens of methods and concluded that the biweight with a window of about **three times the transit duration** is the best general choice.

### What the project measured

- A 1,500 ppm box transit with no variability: a **0.5-day** window loses 8 % of the depth for a 3 h transit and **40 %** for a 5 h one; a **1.0-day** window loses 0 % and 6 %. Transits with periods above 10 days around Sun-like stars last 5 to 6 hours: the default window is 1.0 day.
- **TOI 862.01** (5,092 ppm) disappears with 1.0 day (the curve's spread stays well above the point-to-point noise: leftover fast variability) and shows up with 0.5 day, SDE 18.
- **TOI 190.01** (5.7 h, 8,248 ppm) shrinks to 347 ppm with a 0.3-day window.

No single window works for both cases. The solution: if the ratio of the curve's spread to the point-to-point noise goes above 1.2 (`red_noise_max`), redo the detrending with 0.5 and 0.3 day (`fallback_windows_days`) and **search all versions**. Together with other changes, this took recall from 86.7 % to 88.9 %.

The ratio itself had a trap. With the standard deviation, a deep transit in pure white noise gave a ratio above 3, so the stars with the deepest transits were sent to the short windows that eat transits. Since 2026-10-10 both terms use the MAD, which a few in-transit points cannot move (300 sector 69 stars: 18.7 % flagged with the standard deviation, 16.0 % with the MAD; all 8 stars that changed have deep dips, and 5 of them are TOIs).

**Flattening for vetting.** After detection, the duration and transit times are known, so the vetting can do better than the search: it flattens each sector with that sector's own window, never shorter than 3 × T14, and **masks** the transits so the biweight interpolates across them (Hippke et al. 2019). With a 12 h transit, a plain 1.0-day window keeps 50 % of the depth; the masked flattening keeps 99 %.

The case that still fails: **TOI 251.01** (845 ppm, 4.94 d), a young star with red noise of 1.8, exactly where a GP might help. The history lists it as the "next hypothesis". A hypothesis, not a solution: only the benchmark will tell.

## 5. Single transits and double transits: the niche with the most planets left to find

A **single transit** (monotransit) is one transit observed on its own. A **double transit** (duotransit) is two transits separated by a long gap, usually in sectors from different years, with no transit observed in between.

### Why it is the most promising niche

1. **TESS observes in blocks of about 27 days.** A 60-day planet shows at most one transit per sector, and over much of the sky the star is only observed again years later.
2. **The official pipelines require at least two transits.** Single events are left out.
3. **The evidence is concrete.** Of the TOIs that started out as community CTOIs (168 up to 2021, Zenodo 5130660), most are faint stars from the full-frame images or **single transits rejected by periodic searches**.
4. **Long-period planets are valuable**: they are cooler and less irradiated.

On the other hand, without a period the odd/even, secondary and consistency tests do not exist; and a single event is easy to fake (a pointing adjustment, scattered light, an asteroid crossing the region used to estimate the sky background).

### Estimating the period from the duration

The duration of a central transit ($b = 0$) on a circular orbit is $T \approx P R_\star / (\pi a)$. Combining this with Kepler's third law, $a^3 = G M_\star P^2 / (4\pi^2)$, and solving for $P$:

$$
P \approx \frac{\pi \, G M_\star \, T^3}{4 \, R_\star^3} .
$$

If the transit is not central ($b > 0$), it is shorter than it would be with $b = 0$ for the same period. So using the observed duration in this formula gives a **lower limit** on the period. This idea (estimating the period from the shape of a single transit and the density of the star) is the basis of work such as Osborn et al. (2016), *MNRAS* 457, 2273, done with K2 data.

### Double transits: a comb of aliases

With two transits separated by $\Delta t$, the true period is $\Delta t / n$ for some integer $n$. Each $n$ is a candidate. The lower limit from the duration cuts the large values of $n$. The TESS sectors in which the star was observed without a transit cut others: if alias $n$ predicts a transit on a date with data and nothing shows up, it is ruled out.

### Status in the project

PlanetHunter does **not yet have** a single-transit detector. Today, `n_transits` vetoes any signal with fewer than two transits. But the foundation already respects this niche: `edge_cutoff_days: 0.0` in the detrending keeps events near the edges of the data, precisely so as not to erase single transits. The detector is in phase 4 of the plan.

## 6. The limits of the project's search

| Parameter | Value | Why |
|---|---|---|
| `period_min_days` | 0.2 | Absolute floor of the grid |
| `roche_min_a_rstar` | 2.0 | Shortest orbit: 2 stellar radii (QLP) |
| `period_max_fraction_of_span` | 0.9 | Two transits must fit in the data span |
| `n_transits_min` (TLS) | 1 | Lets the 0.9 limit above take effect; the vetting still requires 2 transits |
| `period_max_days` | 40 | Absolute ceiling, explained below |
| `max_signals_per_target` | 3 | Iterative search: find, mask 2 durations around it, search again |
| `bin_minutes` | 10 | Speeds up the search; loses little for periods above 1 day |

In a single sector (about 27 days), the effective maximum period is 0.9 × 27 ≈ 24 days. (Until 2026-10-10 it was really about 13.5 days: TLS's own default demands room for two transits, which caps the period at half the span, and the 0.9 setting did nothing.) The 40-day ceiling only bites in the **multi-sector** search. And it did bite: when stitching sectors separated by years (about 800 days in total), **spurious aliases of 26 to 64 days** appeared, with one or two transits (TIC 41230546 and 31929204). The mechanism is the double-transit comb: with two distant blocks of data, many periods $\Delta t / n$ line up a noise dip in one sector with another in the other sector, and with thousands of tries some alignment happens. The ceiling cuts the problem at the root; long periods are left for the future single- and double-transit detector.

Another limit: with few transits and gaps, TLS sometimes returns one third of the period (TOI 899.01, 924.01 and 3262.01 showed up at around 4.2 days). The `refine_alias` function tests $2P$ and $3P$: if the epochs predicted only by the short period fall on stretches with data and no dip, the longer period wins. This fix brought recall to 91.1 %. One detail was missing until the audit: after switching to $kP$, the SNR stayed at the value measured with the $P$ epochs, too low by $\sqrt{n_A/n}$ (0.58 for $k = 3$). It is now measured again on the epochs of the true period.

!!! tip "In the tool"
    - All the parameters in this lesson are in `config/thresholds.yaml`, sections `preprocess` and `search`, each with a comment explaining why.
    - The detrending and the window variants are in `src/planethunter/preprocess/clean.py`; the TLS search and `refine_alias`, in `src/planethunter/search/tls.py`.
    - In the dossier, the "Light curve" plot shows the result of the detrending. Compare it with the raw curve and look for shrunken transits.
    - `uv run planethunter run-target 261136679` runs the multi-sector search on Pi Mensae; watch the iterations.

!!! example "Exercise 1. The SNR hidden in BLS"
    A star has a noise of 1,000 ppm per 2-minute point. The sector has $N = 18{,}000$ valid points. A planet with a 5-day period produces transits of 1,000 ppm and 3 hours. Compute $r$, the improvement $\sqrt{\Delta\chi^2}$ predicted by BLS and say whether the signal passes the project's SNR limit.

    ??? success "Show answer"
        1. Fraction in transit: $r = 3\ \text{h} / (5 \times 24\ \text{h}) = 3/120 = 0.025$.
        2. $\sqrt{\Delta\chi^2} = (\delta/\sigma)\sqrt{N r (1-r)} = (1000/1000)\sqrt{18{,}000 \times 0.025 \times 0.975}$.
        3. $18{,}000 \times 0.025 = 450$ points in transit; $450 \times 0.975 = 438.75$; square root $\approx 20.9$.
        4. SNR ≈ 21, well above 7.1. It passes.

        Note: 10-minute bins (5 points) reduce the noise per point to $1000/\sqrt{5} \approx 447$ ppm, but divide $N$ by 5. With white noise, the SNR stays the same: binning speeds things up without losing sensitivity.

!!! example "Exercise 2. Minimum period of a single transit"
    You see a single 10-hour transit on a star just like the Sun ($M = 1\,M_\odot$, $R = 1\,R_\odot$). Use $G M_\odot = 1.327 \times 10^{20}\ \text{m}^3/\text{s}^2$ and $R_\odot = 6.957 \times 10^{8}\ \text{m}$. What is the shortest period compatible with a circular orbit?

    ??? success "Show answer"
        1. $T = 10\ \text{h} = 36{,}000\ \text{s}$; $T^3 = 4.666 \times 10^{13}\ \text{s}^3$.
        2. $R_\star^3 = (6.957 \times 10^8)^3 = 3.367 \times 10^{26}\ \text{m}^3$.
        3. Numerator: $\pi \times 1.327 \times 10^{20} \times 4.666 \times 10^{13} = 1.945 \times 10^{34}$.
        4. Denominator: $4 \times 3.367 \times 10^{26} = 1.347 \times 10^{27}$.
        5. $P \approx 1.444 \times 10^{7}\ \text{s} \approx 167$ days.

        Since $b > 0$ shortens the transit, the real period is **at least** about 167 days (circular orbit). Sanity check: Earth's transit lasts about 13 hours; $(13/10)^3 \times 167 \approx 367$ days, close to the real year.

!!! example "Exercise 3. The comb of a double transit"
    The same star from exercise 2 shows a second, identical transit 730.0 days after the first one, in a sector two years later. List the possible periods. Then suppose TESS observed the star in an intermediate sector in which the 365-day alias predicts a transit in the middle of the data, and nothing showed up. What is left?

    ??? success "Show answer"
        1. Candidates: $P_n = 730.0/n$.
        2. From exercise 2, $P \gtrsim 167$ days, so $n \le 730/167 \approx 4.4$, that is, $n \in \{1, 2, 3, 4\}$.
        3. Periods: 730.0; 365.0; 243.3; 182.5 days.
        4. The intermediate sector rules out $n = 2$ (365 days). Careful: it also rules out $n = 4$, because every transit predicted by 365 days is also predicted by 182.5 days (182.5 is half of 365).
        5. That leaves 730.0 and 243.3 days. Deciding between them requires observing on a date predicted by one and not by the other: this is how double transits turn into requests for ground-based observations.

!!! warning "Common pitfall"
    Concluding that the period is right because the peak is high. It may be $P/2$, $2P$, $P/3$, a multi-sector alias or transits of **two different planets** combined (the HD 23472 case, lesson A2).

## Lesson checklist

- [ ] I did the first and second passes of Kovács, Zucker & Mazeh (2002).
- [ ] I can derive, with the help of this lesson, why maximizing $s^2/[r(1-r)]$ is equivalent to maximizing the SNR of a box.
- [ ] I read Hippke & Heller (2019), this time with the equations, and can name the three main differences from BLS.
- [ ] I can explain with the project's numbers why the detrending window is 1.0 day and when the system uses 0.5 and 0.3.
- [ ] I can estimate the minimum period of a single transit and list the aliases of a double transit.
- [ ] I know why the `period_max_days: 40` ceiling exists.

## Going further

- Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. The original BLS paper, with all the statistics in this lesson.
- Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39. TLS; read the methods section and the comparison with BLS.
- Ofir (2014), *Astronomy & Astrophysics* 561, A138. How to choose the period grid optimally; TLS uses this idea.
- Hippke et al. (2019), *The Astronomical Journal* 158, 143. The wotan paper, with the comparison of detrending methods that justifies the biweight.
- Foreman-Mackey et al. (2017), *The Astronomical Journal* 154, 220. celerite, fast Gaussian processes; a starting point for testing GPs on active stars.
- Osborn et al. (2016), *Monthly Notices of the RAS* 457, 2273. Single transits in K2 and estimating the period from a single event.
- Seager & Mallén-Ornelas (2003), *The Astrophysical Journal* 585, 1038. The analytic relations between transit shape, stellar density and period, the basis of the formula in exercise 2.
