# Intermediate level self-assessment

<p class="meta">Intermediate level · week 10 · about 3 hours</p>

!!! abstract "How to do it"
    - Answer in writing, without looking at the lessons. A calculator is allowed.
    - Only then open each answer and compare. Getting the conclusion right is not enough: the reasoning has to be there.
    - Questions 1 to 6 come from the study plan and decide whether you pass. Questions 7 to 10 are extra practice.

## Passing criterion

**Answer at least 5 of the first 6 questions well** and move on to the [advanced level](../advanced/index.md).

"Answering well" means: the answer names the right mechanism and, when there is a calculation, the calculation reaches the right order of magnitude. If you get two or more wrong, go back to the lessons pointed to in each answer and redo their exercises before trying again.

## Questions from the study plan

!!! question "1. Why does the system require SNR ≥ 7.1 and not ≥ 3?"

    ??? success "Show answer"
        Because of the **look-elsewhere effect**. With Gaussian noise, a 3-sigma value shows up by chance about 1 time in 740. That sounds rare, but the search tests thousands of periods and, for each one, thousands of positions and durations, on about 20,000 stars per sector. That is millions of trials: with a 3-sigma limit, pure noise would produce thousands of "signals" per sector.

        At 7.1 sigma, the chance per trial drops to about $6 \times 10^{-13}$. The value comes from the Kepler mission (Jenkins, Caldwell & Borucki, 2002), chosen so that a search the size of Kepler's, on Gaussian white noise, would produce less than one false alarm in total.

        Bonus point: real noise is not Gaussian. The project measured that searches over a narrow range of periods, on stars with no signal, exceed SNR 19 in 10% of trials. That is why 7.1 is **necessary, but not sufficient**: vetting and the other-sectors test do the rest.

        Review: [M1](m1-statistics-for-signals.md), sections *The normal distribution and "sigma"* and *SNR and the square root of N*.

!!! question "2. A transit lasts 6 hours on a red dwarf with a 3-day period. Why is this suspicious?"

    ??? success "Show answer"
        Because the predicted duration is much shorter. Take a typical red dwarf, with 0.3 R☉ and 0.3 M☉. Its density is $0.3/0.3^3 \approx 11$ times the Sun's.

        $a/R_\star = 215 \times (3/365.25)^{2/3} \times 11^{1/3} \approx 215 \times 0.0407 \times 2.23 \approx 19.5$.

        $T_{14}(b=0) \approx (P/\pi)(R_\star/a) = (3/\pi)/19.5 \approx 0.049$ d $\approx$ **1.2 hours**.

        Six hours is five times that. A central transit is the longest possible on a circular orbit, so a ratio of 5 goes far beyond the 1.67 limit of the `duration` test. Possible explanations:

        - the signal comes from **another star**, a larger one, in the same pixel (a blend);
        - the star is not a red dwarf (wrong radius in the TIC);
        - the period is wrong (the duration grows with $P^{1/3}$; for 6 h on this star, the period would have to be hundreds of days);
        - a very eccentric orbit, which rarely explains a factor of 5.

        Review: [M2](m2-transit-physics.md), section "The transit duration".

!!! question "3. What changes in the periodogram if the curve has a big gap in the middle?"

    ??? success "Show answer"
        Several things, all for the worse:

        - **Fewer transits.** The ones that fall in the gap do not exist in the data. The SNR drops (fewer points) and, with a long period, only one transit may be left, which `n_transits` vetoes.
        - **Stronger aliases.** The "extra" transits predicted by P/2 or P/3 may fall in the gap, and nothing in the data contradicts them. The alias peak becomes as high as the true one, or higher. This is what happened with TOI 899.01, 924.01 and 3262.01 in sector 69, found at about 4.2 d instead of 12 to 13 d. `refine_alias` tests 2P and 3P for exactly this reason.
        - **New edges.** Each side of the gap is a segment edge. Detrending creates ramps there that can mimic transits (the project measured SDE ~10 in pure noise with an event 0.07 d from the edge). Signals with more than 50% of their transits at edges are blocked (`edge_transit_fraction`).
        - **Structure in the periodogram.** Periods that put all the transits in the gap cannot be tested; the periodogram ends up with more spurious peaks tied to the spacing of the segments.

        Review: [M3](m3-periodograms.md), sections "Aliases: the ghost peaks" and "Gaps and segment edges".

!!! question "4. Why does the centroid test use the implied source distance and not just the significance of the shift?"

    ??? success "Show answer"
        Because **significance** answers "does the shift exist?", not "is the source far away?". On bright stars, with many transits, the centroid error becomes tiny, and even an irrelevant shift, caused by the target itself, becomes more than 3 sigma.

        The **implied distance** answers the right question. If a source at a distance $D$ from the centroid dims with relative depth $\delta$, the centroid moves by about $\delta \times D$. So $D \approx$ shift / depth. If $D$ is less than 1 pixel (21″), the source is compatible with the target.

        The measured evidence: with the significance-only criterion, **11 of 41 confirmed planets** in sector 69 failed, all with the implied source at most 0.88 pixel away. The current rule requires both: more than 3 sigma **and** a source more than 1 pixel away. A false positive like TOI-854.01 (12σ, source 2.0 pixels away) still fails. Two refinements make the sigma itself honest: the error of one epoch is measured at 200 fake epochs outside the transits, and the depth is corrected to the depth inside the aperture (CROWDSAP × δ).

        Review: [M5](m5-vetting-in-practice.md), section `centroid`.

!!! question "5. Explain, with a drawing, why a binary with period 2P shows different depths in odd and even transits."

    ??? success "Show answer"
        An eclipsing binary has **two** eclipses per orbit: the primary (the brighter star is covered) and the secondary (the fainter star is covered). If the stars are similar, the two eclipses have similar depths, and the search finds the interval between consecutive eclipses, P. The true orbital period is **2P**.

        ```
        brightness
        ────╮    ╭────╮  ╭────╮    ╭────╮  ╭────
            │    │    ╰──╯    │    │    ╰──╯
            ╰────╯            ╰────╯
              1        2        3        4
             odd      even     odd      even
            deep    shallow   deep    shallow
              |<- P -->|<- P -->|
              |<----- 2P ------>|
        ```

        With period P, we number the events 1, 2, 3, 4... The odd ones (1, 3, 5) are always primaries; the even ones (2, 4, 6), always secondaries. If the stars differ in size or temperature, the primaries are deeper than the secondaries, and the average of the odd events differs from the average of the even ones.

        The `odd_even` test measures this difference in sigmas (with the block error): it fails from 3σ and vetoes from 5σ. Real example: TOI-343.01, odd 2,294 ppm, even 4,583 ppm, 5.8σ, vetoed.

        Review: [M3](m3-periodograms.md), the warning "Binary with period 2P", and [M5](m5-vetting-in-practice.md).

!!! question "6. Open a dossier that passed and say which test you would do next before submitting."

    ??? success "Show answer"
        There is no single answer, but a good answer follows this logic:

        1. **See what is pending.** The vetting table lists the deep tests that have not run yet (`tpf_difference_image`, `gaia_neighbors`, `fpp_triceratops`). A signal that passed basic vetting has not been through them yet.
        2. **The most powerful test is usually other sectors.** If the star was observed in other sectors, the signal has to show up again with the expected strength. This test is what knocked down HD 271883 (signal 1798, 6.61 d): expected SNR 45 to 64 in sectors 67, 68 and 97, and the signal did not appear. Run `uv run planethunter vet-deep <run_id>`.
        3. **Then, the TPF difference image and Gaia neighbors**, to confirm that the source is the target.
        4. **Then, FPP with triceratops**, only if everything above passes.
        5. **And always:** the star's page on ExoFOP and a search on ADS for the TIC, to see whether someone has already published it.

        A strong answer cites the specific dossier: "this star has a known host and 3 other sectors; the next step is `vet-deep` for the other-sectors test, because a new, deep signal in a single sector is the classic signature of a systematic".

        Review: [M5](m5-vetting-in-practice.md), "Candidate review routine", and step 6 of the beginner's guide.

## Extra questions

!!! question "7. A code change moved recall from 120/135 to 123/135. Does this prove the change improved the system?"

    ??? success "Show answer"
        Not on its own. The 95% confidence interval (Wilson) for 123/135 goes from 85.1% to 94.8%; for 120/135 (88.9%), the simple approximation gives 83.6% to 94.2%. The intervals overlap almost completely: three more TOIs are compatible with chance.

        What makes the change convincing is the **diagnosis**: knowing which TOIs started being found and why. In the benchmark history, the change in the final run (`refine_alias`) recovered exactly TOI 899.01, 924.01 and 3262.01, which before came out at P/3. An identified cause plus an effect in the predicted place: that is convincing.

        Review: [M1](m1-statistics-for-signals.md), "Binomial confidence interval: how much to trust a recall".

!!! question "8. What would happen if the detrending window were 0.2 day?"

    ??? success "Show answer"
        The filter would start following the transit itself and "eating" it. The rule of thumb is a window of about 3 times the transit duration: 0.2 d (4.8 h) only preserves transits of up to ~1.6 h well.

        The measured numbers show the size of the damage with windows larger than that: with 0.5 d, a 5 h transit loses 40% of its depth; with 0.3 d, TOI 190.01 (5.7 h) dropped from 8,248 ppm to 347 ppm. With 0.2 d, transits of 3 h or more would be strongly reduced, the SNR would drop and many planets with periods above a few days would disappear.

        In exchange, very variable stars would come out cleaner. That is why PlanetHunter only uses short windows (0.5 and 0.3 d) in a **second variant**, when the noise ratio goes above 1.2, and searches both versions.

        Review: [M3](m3-periodograms.md), "Detrending: the window that decides".

!!! question "9. A planet with a 10-day period transits a star identical to the Sun, and the measured transit lasts 3.0 hours. Does the duration test pass? What is the approximate impact parameter?"

    ??? success "Show answer"
        Predicted with $b = 0$: $a/R_\star \approx 19.5$ and $T_{14} \approx (10/\pi)/19.5 \approx 0.163$ d $\approx$ 3.9 h.

        Ratio: 3.0/3.9 ≈ 0.77. It is between 0.15 and 1.67: **it passes**.

        With $T_{14}/T_{14}(b=0) \approx \sqrt{1-b^2}$: $1 - b^2 = 0.77^2 \approx 0.59$, so $b \approx 0.64$. An off-center transit, perfectly normal.

        Review: [M2](m2-transit-physics.md), exercises 1 and 3.

!!! question "10. A NEW signal fails secondary (4σ, 6% of the primary) and edges_dumps; the centroid had no data. Calculate the score, the verdict and the severity."

    ??? success "Show answer"
        `secondary` at 4σ is a failure (≥ 3σ), with no veto (it does not reach 5σ and is below 10%): weight 0.4. It is not a case of period halving either, because 6% is far from the primary's depth. `edges_dumps` failed: weight 0.4. `centroid` with no data: 0.95, but "no data" is not a failure.

        Score = 0.4 × 0.4 × 0.95 ≈ **0.15**. Verdict: **FAIL**, because there are two soft failures and only one is tolerated. It does not become a candidate, so it has no severity. (If the calibrated model gave it a `p_rank` above its P2 threshold, it could be rescued, but only up to P2.)

        Note that no test vetoed, but two soft failures were enough. It also makes sense from the physics: a dip at phase 0.5 and transits at edges are, together, an unconvincing profile.

        Review: [M5](m5-vetting-in-practice.md), "The verdict and the score".

## Next step

Passed? The [advanced level](../advanced/index.md) takes you to the original papers (BLS, TLS, Robovetter, triceratops), to the calculation of the false positive probability, to the benchmark with injected synthetic transits and to preparing a CTOI submission.

Before you go, keep your intermediate-level review notebook. It will be the starting material for the machine learning lesson.
