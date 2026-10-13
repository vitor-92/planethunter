# A5. Measuring the system: completeness and benchmarks

<p class="meta">Advanced level · weeks 11–13 · about 14 hours</p>

!!! abstract "In this lesson you will learn"
    - The difference between recall, completeness and precision, and which question each one answers.
    - How the project's recall benchmark works and why the main metric is recall on the TOIs that are "detectable in one sector".
    - How to compute the Wilson interval by hand and why it is better than the "plus or minus" interval.
    - How injection-recovery is done: parameter grid, injection into the raw flux, recovery criterion.
    - What the noise floor measured by the project is (median 5.2; p90 19; p99 98) and why a fixed limit does not work.
    - The before/after method for changing a limit, and how to do it yourself.

One project rule sums up this lesson: **changing the search or the vetting requires rerunning the benchmark and attaching the before and after**. Without measurement, a change is just an opinion.

## 1. Three questions, three metrics

| Metric | Question | How it is measured |
|---|---|---|
| **Recall** | Of the real objects in the set, how many does the system find? | Recovered ÷ total known real objects |
| **Completeness** | How does recall vary with period, radius, star brightness? | Recall per cell of a parameter grid, usually with injections |
| **Precision** | Of the alerts the system sends, how many are real? | Confirmed alerts ÷ alerts sent (requires human review or follow-up) |

Recall and precision pull in opposite directions. Loosening a limit raises recall and lowers precision. Every change must measure both, or a reasonable stand-in for the second. In vetting, the project uses the **pass rate of `KNOWN_FP`** as a stand-in: if it goes up, the vetting has become too loose.

## 2. The project's recall benchmark

The code is in `src/planethunter/benchmark.py`. The procedure:

1. **Freeze a list** (`benchmark build`). From ExoFOP, take the TOIs with disposition CP, KP or PC, "Planet SNR" ≥ 10 and period between 0.5 and 13 days that were observed in sector 69. Result: **220 TOIs**. The list is saved as a CSV and never changes again, so that different runs can be compared.
2. **Run the search** only on these targets (`benchmark run`). **185** have a 2-minute SPOC light curve.
3. **Evaluate**: a TOI is recovered if some signal in the run matches its period (alias 1, 2 or 1/2) **and** its phase. Aliases 3, 1/3, 3/2 and 2/3 are counted separately, as "found with an ambiguous period".

### Why "detectable in one sector"

In the first run, 68 TOIs were missed. On investigation, **55 of them had an expected SNR below 7 with sector 69 data alone**. ExoFOP's "Planet SNR" adds up all the sectors in which the star was observed. With a single sector, no pipeline would find these objects. Counting them as failures would measure the size of the data set, not the quality of the search.

That is why the benchmark computes, for each TOI, the **expected SNR** in this sector:

$$
\text{SNR}_\text{expected} = \frac{\delta}{\sigma_\text{p2p}} \sqrt{N_\text{in transit}},
\qquad
\sigma_\text{p2p} = \frac{\text{standard deviation}(\text{differences between neighboring points})}{\sqrt{2}} ,
$$

using the catalog depth, the point-to-point noise of the processed curve and the number of points that fall inside the predicted transits. A TOI is **detectable** if the expected SNR is ≥ 7.1 and there are at least 2 epochs with data. There are **135** of them. Point-to-point noise is used because it is not very sensitive to slow variations: it measures the "hiss" from one point to the next.

### The history

| Run | Change | Recall on detectable |
|---|---|---|
| baseline | 1.0 d window, stellar limits ±30 % | 114/135 = 84.4 % |
| 2 | wide duration grid + adaptive window | 117/135 = 86.7 % |
| 3 | detrending variants (combined) + stellar model capped at 1.5 | 120/135 = 88.9 % |
| 4 | `refine_alias` + `period_max` 0.9 × span | **123/135 = 91.1 %** (95 % CI 85.1–94.8 %) |

And by depth, in the final run:

| Depth (ppm) | Recovered | Total | Recall |
|---|---|---|---|
| 0–500 | 6 | 10 | 60 % |
| 500–1,000 | 11 | 13 | 85 % |
| 1,000–3,000 | 19 | 23 | 83 % |
| 3,000–10,000 | 34 | 36 | 94 % |
| above 10,000 | 53 | 53 | 100 % |

The plan's goal is ≥ 90 %. The overall number passes, but the table shows where the problem is: shallow transits. That is where the next piece of work pays off.

## 3. The Wilson interval

With 135 objects, 91.1 % is not an exact number. If the project ran on another sector with another 135 TOIs, the result would be a little different. The **confidence interval** tells you by how much.

The "naive" interval ($p \pm 1.96\sqrt{p(1-p)/n}$) fails exactly where it matters most: near 0 % or 100 % and with small samples. With 53 out of 53, it gives zero width, as if 100 % were a certainty. The **Wilson interval** (Wilson 1927) fixes this. With $p = k/n$ and $z = 1.96$ for 95 %:

$$
\text{center} = \frac{p + \dfrac{z^2}{2n}}{1 + \dfrac{z^2}{n}},
\qquad
h = \frac{z\sqrt{\dfrac{p(1-p)}{n} + \dfrac{z^2}{4n^2}}}{1 + \dfrac{z^2}{n}},
\qquad
\text{CI} = [\text{center} - h,\ \text{center} + h] .
$$

This is exactly what the `wilson` function in `benchmark.py` computes.

### The calculation for 123 out of 135

1. $p = 123/135 = 0.9111$; $z^2 = 3.8416$; $z^2/n = 0.02846$; denominator $= 1.02846$.
2. Center: $(0.9111 + 3.8416/270)/1.02846 = (0.9111 + 0.01423)/1.02846 = 0.8997$.
3. $p(1-p)/n = 0.9111 \times 0.0889/135 = 0.000600$; $z^2/(4n^2) = 3.8416/72{,}900 = 0.0000527$; sum $0.000653$; square root $0.02555$.
4. $h = 1.96 \times 0.02555 / 1.02846 = 0.0487$.
5. CI $= [0.851,\ 0.948]$, or **85.1 % to 94.8 %**. It matches the report.

Notice that the center (90.0 %) is a little lower than $p$: Wilson "pulls" the estimate away from the extremes, which is honest with finite samples.

## 4. Injection-recovery

The TOI benchmark measures the system **on what is already known**. But TOIs are, in general, deep and around bright stars. To measure the niches where the project wants to find new things (shallow, long-period, faint stars), there are not enough TOIs. The solution is to manufacture the test: **inject synthetic transits into real curves** and see which ones the system recovers. It is the same principle Kepler used to measure the completeness of its pipeline (Christiansen et al. 2013).

The recipe is in the project's `injection-recovery` skill:

**Where to inject.** Into the **raw** flux, before detrending. That way the measurement includes the loss caused by the detrending itself, which lesson A1 showed can be large (up to 40 % with a short window).

**How to generate.** With the `batman` library (Kreidberg 2015): a transit model with quadratic limb darkening, coefficients chosen from the star's temperature, $a/R_\star$ computed from the stellar density and a randomly drawn impact parameter.

**The grid.**

| Axis | Values |
|---|---|
| Period (d) | 0.5; 1; 2; 4; 8; 13; 20; 27; 40 |
| Planet radius (R⊕) | 1; 1.5; 2; 3; 4; 6; 10; 15 |
| Impact parameter $b$ | 0; 0.3; 0.6; 0.9 |
| Target Tmag | 8–10; 10–12; 12–13.5; 13.5–15 |

**The curves.** 200 real curves **with no signal** (SDE < 6 in the original search) per Tmag range. At least 50 injections per cell, with a random epoch.

**The criterion.** Recovered if the period found is within 1 % of the injected one (or alias 2 or 1/2) and the SDE passes the limit. Also keep the measured depth and SDE, to estimate the bias (does detrending shrink transits?).

**The report.** A completeness map (period × radius) per Tmag range, with a Wilson interval in each cell.

Status in the code: the recall benchmark is implemented; injection-recovery with a grid is **not yet**. It is the next step, and a great project for anyone who finishes this level.

## 5. The noise floor: 5.2, 19 and 98

The `other_sectors` test (lesson A2) looks for the signal in other sectors with a search **in a narrow band** around the period: 300 periods within ±1 % of $P$ and another 300 around $2P$, with three durations. It looks like a small search. It is not.

The project measured what this search finds **on stars with no signal**, in 144 tries with random periods in sector 69. The SNR of the best peak:

| Statistic | SNR found in noise |
|---|---|
| Median | 5.2 |
| 90th percentile | 19 |
| 99th percentile | 98 |

In 10 % of the tries, noise alone gave an SNR above 19. In 1 %, above 98. Two causes add up: the look-elsewhere effect (hundreds of periods, several durations, every phase, and the maximum is kept) and **red noise** with residual systematics, which produces coherent dips lasting several hours.

The consequence: **a fixed SNR limit does not work** for deciding whether the signal "showed up" in another sector. The project measures the floor **of each star**: it runs the same search at 40 random periods (between 0.6 and 1.7 times $P$, away from $P/2$, $P$ and $2P$) and uses the 90th percentile as the floor. Before measuring it, the candidate's own transits are masked. Without the mask, a strong signal raised its own floor (an SNR of 2,192 against a floor of 2,272), and 16 of 24 failures of this test were false. An absence only counts as evidence if the expected SNR is at least 10 **and** at least 1.5 times the floor. A veto requires a decisive absence in at least two sectors.

The real cases show both sides:

- **HD 271883** (signal 1798, 6.61 d): expected SNR of 45 to 64 in sectors 67, 68 and 97. It did not show up. Decisive absence: veto.
- **Signal 1634** (11.35 d): expected SNR of 12 and 9 in sectors 95 and 96, with floors of 13.5 and 11.6. The absence there is **not evidence**: the star's own noise would produce peaks that size. The decision came from the blind search in sectors 95 to 97, which recovered neither 11.35 nor 22.7 days.

## 6. The before/after method

For any change to `config/thresholds.yaml` or to the search and vetting code:

1. **A hypothesis with a mechanism.** Not "I think 1.2 is better than 1.3", but "TOIs X and Y are missed because the detrending leaves variability behind; reducing the window on these stars should recover them".
2. **Success and give-up criteria, written in advance.** For example: "I accept if recall on detectable TOIs does not drop and at least 2 of the 11 missed ones are recovered; I give up if any `KNOWN_PLANET` gets vetoed".
3. **The same frozen list and the same mirrors.** Write down the `params_hash` and the `pipeline_version` that the report records.
4. **One change at a time.** Two changes together make it impossible to know which one did what.
5. **Run before and after** with the same code, except for the change.
6. **Compare in pairs.** The two runs use the **same** objects. Comparing the confidence intervals is not enough, since they almost always overlap. List the objects that **changed status**: gains and losses.
7. **Measure the other side.** Pass rates of `KNOWN_PLANET` and `KNOWN_FP` (the `vet` table), search time.
8. **Write** `docs/benchmarks/<date>-<sha>.md` with a before/after table, a list of status changes and the decision.

### Paired comparison in one line

Suppose the change made $g$ objects go from missed to recovered and $l$ go the other way. If the change had no effect at all, each of these $g + l$ cases would have a 50 % chance of going either way. The probability of such an unbalanced result by chance is given by the exact **McNemar test**, a coin-flip calculation:

$$
p = 2 \times P\big(X \ge \max(g, l)\big), \qquad X \sim \text{Binomial}(g + l,\ 0.5) .
$$

!!! tip "In the tool"
    - `uv run planethunter benchmark build 69` freezes the list of planets; with `--kind fp`, the list of TFOPWG false positives.
    - `uv run planethunter benchmark run 69 --skip-ingest` redoes the search and writes the report to `docs/benchmarks/`. With `--run <run_id>`, it only re-evaluates an existing run.
    - `uv run planethunter vet <run_id>` prints the validation table by class (`KNOWN_PLANET`, `KNOWN_FP`...).
    - The existing reports: `2026-10-09-s0069-history.md` and `2026-10-09-s0069-vetting.md`.

!!! example "Exercise 1. One hundred percent, but how much?"
    In the depth range above 10,000 ppm, recall was 53/53. Compute the lower limit of the Wilson interval.

    ??? success "Show answer"
        With $k = n$, $p = 1$ and the term $p(1-p)/n$ vanishes. Then $h = (z^2/2n)/(1 + z^2/n)$ and the center is $(1 + z^2/2n)/(1 + z^2/n)$. The lower limit becomes:

        $$
        \frac{1}{1 + z^2/n} = \frac{1}{1 + 3.8416/53} = \frac{1}{1.0725} \approx 0.932 .
        $$

        "100 %" means, with 95 % confidence, **at least 93 %**. The naive interval would say "100 % ± 0", which is false.

!!! example "Exercise 2. Is it worth tightening the V-shape test?"
    The project changed `v_shape_max` from 0.45 to 0.35. With 0.45, the `shape` test caught none of the 18 TFOPWG FPs. With 0.35, it catches 8 of 18 and flags 3 of 50 planets (HIP 65 A b, LTT 9779 b and TOI-2382 b, all grazing). (a) Compute the Wilson CI for 8/18. (b) Is the change justified? What precaution was taken?

    ??? success "Show answer"
        (a) $p = 0.444$, $z^2/n = 0.2134$, denominator $1.2134$. Center $= (0.444 + 0.1067)/1.2134 = 0.454$. $p(1-p)/n = 0.01372$; $z^2/(4n^2) = 0.00296$; sum $0.01668$; square root $0.1292$; $h = 1.96 \times 0.1292/1.2134 = 0.209$. CI $\approx$ **25 % to 66 %**. With 18 objects, the uncertainty is huge.

        (b) Even in the worst case (25 %), going from 0 to at least a quarter of the FPs is a real gain. The cost is 3 grazing planets flagged. The precaution at the time: the test became a **soft fail** (weight 0.5 in the score), not a veto, so a grazing planet could stay in the queue if everything else was clean. Since the 2026-10-10 audit `shape` is a **hard fail** (a failure alone fails the verdict, still not a veto): measured on sectors 69 and 107, it costs about 3 grazing planets per sector and stops 4 to 9 eclipsing binaries found at half their period. Both decisions are commented in `config/thresholds.yaml`, with names and numbers.

!!! example "Exercise 3. Are three gains enough?"
    From run 2 to run 3, recall went up from 117 to 120. Suppose 3 TOIs started being recovered and none was lost. (a) What is the McNemar $p$? (b) Does this invalidate the change?

    ??? success "Show answer"
        (a) $g = 3$, $l = 0$. $P(X \ge 3)$ with $X \sim \text{Binomial}(3, 0.5)$ is $0.5^3 = 0.125$. $p = 2 \times 0.125 = 0.25$. On its own, the result is compatible with chance.

        (b) It does not invalidate it. The statistics say that 3 gains prove nothing **by themselves**. But each gain has a mechanism diagnosed in advance (for example, TOI 862.01 only shows up with a 0.5 d window, because of measured fast variability) and there are no losses. A hypothesis with a mechanism + gains in the predicted objects + zero losses is strong evidence. What would be worrying: gains in objects the hypothesis did not predict, or any unexplained loss.

!!! example "Exercise 4. How much does the injection grid cost?"
    How many searches does the full grid in section 4 require with 50 injections per cell? The benchmark searched 185 targets in 1.3 minutes with 15 processes. Estimate the time.

    ??? success "Show answer"
        1. Cells: $9 \times 8 \times 4 \times 4 = 1{,}152$. Injections: $1{,}152 \times 50 = 57{,}600$ searches.
        2. Time per target (wall clock, 15 processes): $1.3 \times 60 / 185 \approx 0.42$ s.
        3. Total: $57{,}600 \times 0.42 \approx 24{,}000$ s, about **6.7 hours** on the same machine.
        4. Doable overnight. In practice, start with one Tmag range and one slice of the grid to validate the code before spending the night.

## Practice: change a limit and measure

Do it on a git branch (`git switch -c experiment-<name>`), never directly on the main branch.

1. Pick **one** vetting limit, for example `duration_ratio_max` (1.67) or `odd_even_fail_sigma` (3.0). Write down the hypothesis and the success and give-up criteria.
2. Build the lists: `uv run planethunter benchmark build 69` and `uv run planethunter benchmark build 69 --kind fp`.
3. Run the search on the targets of both lists (`uv run planethunter search --sector 69 --tics <comma-separated TICs>`), then `crossmatch` and `vet` on the run. Keep the validation table: this is the **before**.
4. Change the limit. Run `vet` again on the same run (vetting changes do not require a new search). This is the **after**.
5. Compare: pass rates of `KNOWN_PLANET` and `KNOWN_FP` with Wilson intervals, and the list of signals whose verdict changed.
6. If you change a search parameter (`window_length_days`, for example), run `benchmark run 69 --skip-ingest` before and after and compare the paired recall.
7. Write a page in `docs/benchmarks/` with the hypothesis, the table, the status changes and the decision. Even if the decision is "I gave up". A well-documented negative experiment saves someone else from repeating it.

## Lesson checklist

- [ ] I know the difference between recall, completeness and precision.
- [ ] I can explain why the main metric is recall on the 135 detectable TOIs, not on the 220.
- [ ] I computed the Wilson interval by hand for 123/135 and for 53/53.
- [ ] I can describe the injection-recovery grid and why the injection goes into the raw flux.
- [ ] I can explain the noise floor (5.2; 19; 98) and how the project uses it.
- [ ] I changed a limit on a branch, measured before and after and wrote the report.

## Going further

- Wilson (1927), *Journal of the American Statistical Association* 22, 209. The original paper on the interval; short and readable.
- Brown, Cai & DasGupta (2001), *Statistical Science* 16, 101. Shows, with plots, why the naive interval fails and why Wilson is a good choice.
- Christiansen et al. (2013), *The Astrophysical Journal Supplement Series* 207, 35. Injecting transits into Kepler pixels to measure the pipeline's recovery; the model for what the project wants to do.
- Burke et al. (2015), *The Astrophysical Journal* 809, 8. How measured completeness goes into the calculation of planet occurrence rates.
- Kreidberg (2015), *Publications of the Astronomical Society of the Pacific* 127, 1161. `batman`, used to generate the synthetic transits.
- McNemar (1947), *Psychometrika* 12, 153. The test for comparing two proportions measured on the same objects.
