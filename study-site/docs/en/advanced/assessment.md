# Advanced level self-assessment

<p class="meta">Advanced level · week 16 · about 6 hours</p>

!!! abstract "How to use this page"
    - The first four questions are the ones from the study plan. The other six cover points from each lesson.
    - Write your answer **before** opening the model answer. Use your reading notebook and your review notebook, but not this page.
    - The questions are open-ended. The model answers show the elements a good answer needs, not the only right answer.

## Questions from the plan

!!! question "Question 1. Propose a change to the vetting"
    Propose a change to PlanetHunter's vetting. Explain the hypothesis, how you would measure the effect and which result would make you give it up.

    ??? success "Show answer"
        A good answer has four parts. A model example:

        **Change.** A new **depth-per-aperture** test: measure the transit depth with the pipeline aperture, with a smaller aperture (only the target's brightest pixels) and with a larger one. Soft fail if the depth grows significantly with the aperture.

        **Hypothesis with a mechanism.** If the transit is on the target, the fractional depth is roughly the same in any aperture centered on it. If it comes from a neighbor at the edge of the aperture, the larger aperture includes more of the neighbor's light and the depth changes. Of the 8 TFOPWG FPs that still pass in sector 69, some are background binaries; the hypothesis is that the test catches some of them.

        **Measurement.** Run the test on the 54 `KNOWN_PLANET` and 18 `KNOWN_FP` signals of the sector 69 vetting benchmark. Metrics: how many of the 8 remaining FPs start failing; how many planets start failing; Wilson intervals. Paired comparison: list of signals whose verdict changed. Report in `docs/benchmarks/`.

        **Give-up criterion, written in advance.** I give up if it catches 0 of the 8 remaining FPs, or if it flags more than 2 of the 54 planets, or if the effect depends on a single object. I also give up if, looking case by case, the FPs it catches were already rejected by another test in the deep vetting (a redundant gain).

        Points the answer must have: a physical mechanism, test sets with a known answer, a metric on both sides (planets and FPs), uncertainty with a small sample and a stopping criterion defined before seeing the result.

!!! question "Question 2. The continuous viewing zone"
    Explain why a new, deep signal on a star in the TESS continuous viewing zone is almost always a systematic.

    ??? success "Show answer"
        1. Stars near the ecliptic poles (the continuous viewing zone) are observed in many sectors. In sector 69, the hosts in this region had **10 to 22 sectors** of data.
        2. A deep signal has a high SNR. If it were real and periodic, it would have shown up in many of those sectors, with a huge SNR when all of them are combined. SPOC, QLP and the community would already have produced a TOI or CTOI. If it is not in any catalog, the simplest explanation is that it **does not exist** in the other sectors.
        3. A signal that shows up in only one sector is the signature of a systematic in that sector: scattered light, a pointing adjustment, a detrending problem at an edge.
        4. Evidence from the project: HD 271883, a clean signal of 6.61 d and 4,900 ppm, passed all the basic tests. In sectors 67, 68 and 97, the expected SNR was 45 to 64. It did not show up. The `other_sectors` test vetoed it.
        5. Exceptions to consider: a single transit with a very long period (rare, because the continuous coverage spans almost a year) or an event that fell into a gap in the other sectors. That is why the test requires a **decisive** absence (expected SNR ≥ 10 and ≥ 1.5 times the noise floor) in at least two sectors, and also runs the blind search.

!!! question "Question 3. Dissect a paper"
    Read a recent validation or confirmation paper for a TESS planet. Identify each vetting test it used and which ones PlanetHunter does not have.

    ??? success "Show answer"
        The answer depends on the paper you choose. Build a table with three columns: test, evidence in the paper (figure or table), equivalent in PlanetHunter. Tests that usually show up:

        | Test in the paper | In PlanetHunter |
        |---|---|
        | SPOC DV report: odd/even, secondary, difference image centroid | `odd_even`, `secondary`, `tpf_difference_image` |
        | DV optical ghost diagnostic | None |
        | Ground-based photometry (SG1): transit on target, neighbors ruled out, depth in several colors | None (out of scope; comes from follow-up) |
        | Reconnaissance spectroscopy (SG2): no spectroscopic binary, stellar parameters | None; uses the TIC |
        | High-resolution imaging (SG3) with a contrast curve | None; triceratops runs without a contrast curve |
        | Binarity indicator from Gaia astrometry (for example, RUWE) | None |
        | FPP with vespa or triceratops | `fpp_triceratops` |
        | Radial velocity (SG4) | None |
        | Consistency between sectors | `other_sectors` |

        The expected conclusion: PlanetHunter covers well the automatic part done only with TESS and Gaia data; it is missing everything that requires another telescope, plus a few DV diagnostics (optical ghost) and astrometry. The answer is good if it says, for each gap, whether it can be implemented in the project or can only be solved through follow-up.

!!! question "Question 4. Write a submission"
    Write the text of a CTOI submission for a hypothetical candidate, using the numbers from the dossier.

    ??? success "Show answer"
        A model, with **hypothetical** numbers from a dossier:

        - **TIC**: XXXXXXXXX
        - **Period**: 9.8714 ± 0.0009 d
        - **Epoch**: 2,460,156.3381 ± 0.0016 BJD (TDB), in the middle of the data
        - **Depth**: 1,240 ± 110 ppm
        - **Duration**: 3.4 ± 0.2 h
        - **Estimated radius**: 3.1 R⊕ for R* = 0.81 R☉ (TIC)
        - **User disposition**: PC

        **Notes**: "Signal found with TLS in the SPOC 2-min light curve of sectors 68–69 (PlanetHunter version X, run Y), 3 transits, SDE 14.2, SNR 11.8. Odd/even: difference 0.6σ. No secondary at phase 0.5 (3σ limit: 180 ppm) or at other phases. U shape (τ/T14 = 0.18). Duration consistent with the TIC stellar density (ratio 0.92). Difference image: centroid 0.15 ± 0.21 px from the target. Gaia neighbors: none able to produce the dip outside the 6″ exclusion radius. Not in catalogs of planets, TOIs, CTOIs or binaries (mirrors 6 h old); ADS and arXiv search on 2026-10-09 with no results. Triceratops: FPP 0.08, NFPP 0.0004, main competing scenario PEB. Limitations: no other sectors with data; no high-resolution imaging. Suggestion: SG1 at the next predicted transit (2,460,412.995 ± 0.023 BJD, 26 orbits after the epoch) and SG3."

        Criteria: epoch in full BJD; uncertainties on every number; tests with values, not adjectives; explicit limitations; correct vocabulary; provenance; a follow-up suggestion with a transit prediction.

## Extra questions

!!! question "Question 5. BLS is an SNR"
    Show, with the box model and equal errors, why maximizing $s^2/[r(1-r)]$ is equivalent to maximizing the SNR of the transit.

    ??? success "Show answer"
        With data centered on zero, depth $\delta$ and in-transit fraction $r$: level inside $L = -\delta(1-r)$, outside $H = \delta r$. Then $s = rL = -\delta\, r(1-r)$ and $s^2/[r(1-r)] = \delta^2 r(1-r)$. Going back from normalized weights to chi-squared with error $\sigma$: $\Delta\chi^2 = N\delta^2 r(1-r)/\sigma^2$. The square root is $(\delta/\sigma)\sqrt{N r(1-r)} \approx (\delta/\sigma)\sqrt{N_\text{in transit}}$, the SNR. Extra point: remember that, with red noise, the per-point $\sigma$ underestimates the error of averages, and the BLS SNR becomes optimistic.

!!! question "Question 6. The catalog that had planets"
    Tell the story of the hot Jupiter problem in the TESS binary catalog and explain the rule that solved it.

    ??? success "Show answer"
        In the sector 69 calibration, the 9 signals that matched the binary catalog of Prša et al. (2022) were confirmed planets, such as WASP-18 b, WASP-100 b and HATS-16 b. Deep transits of hot giants, sometimes with a visible occultation, were included in the catalog by automatic criteria. The fix defines an order of evidence in the crossmatch: confirmed planet > TFOPWG FP/FA > TOI > CTOI > binary catalog. The general lesson: every catalog has a goal and an error rate; the priority must follow the strength of the evidence (a mass measurement beats a shape classification).

!!! question "Question 7. A planet with FPP 0.35"
    The confirmed planet WASP-100 b got an FPP of 0.35 from triceratops (TP 0.54, PEB 0.35, PTP 0.11, NFPP ≈ 0). Does this point to a flaw in triceratops?

    ??? success "Show answer"
        No. The FPP measures what the data **provided** can rule out. With TESS photometry alone, and no contrast curve, the PEB scenario (target with an unresolved bound companion, eclipsed by a star) reproduces a deep transit reasonably well. The radial velocity that confirmed the planet did not go into the calculation. A contrast curve from high-resolution imaging would cut the companion prior and knock out PEB. The negligible NFPP shows that no known neighbor is a suspect. Conclusion: the result is consistent and illustrates why FPP is one test among others, and why validation requires high-resolution imaging.

!!! question "Question 8. The ML that leaked"
    Why must the training and test sets of a signal classifier be split by star, and why, in the project, can ML not veto?

    ??? success "Show answer"
        Split by star: the same star produces several signals (several sectors, several planets, iterations). Splitting by signal, the network recognizes the star in the test (noise, variability, depth) and the measured performance is memory, not generalization.

        No veto: (1) the planets the project is looking for are in the niches with the fewest training examples; (2) vetoing a real planet is irreversible, while reviewing a false one costs minutes; (3) deterministic vetting is auditable and measured by a benchmark; (4) ML does not recover what the search does not detect. ML reorders the queue, keeping recall intact.

!!! question "Question 9. What is 81 % worth?"
    In the vetting benchmark, 44 of 54 confirmed planets were approved (81 %). Compute the 95 % Wilson interval and say what it implies for comparing two versions of the vetting.

    ??? success "Show answer"
        $p = 0.8148$; $z^2/n = 3.8416/54 = 0.0711$; denominator $1.0711$. Center $= (0.8148 + 3.8416/108)/1.0711 = (0.8148 + 0.0356)/1.0711 = 0.794$. $p(1-p)/n = 0.00279$; $z^2/(4n^2) = 0.00033$; sum $0.00312$; square root $0.0559$; $h = 1.96 \times 0.0559/1.0711 = 0.102$. CI ≈ **69 % to 90 %**.

        Implication: two versions with 81 % and 85 % have almost identical intervals. Comparing intervals does not settle it. Since the objects are the same, compare in pairs: list the planets whose verdict changed and use the McNemar test, together with the mechanism behind each change.

!!! question "Question 10. An absence that proves nothing"
    A candidate does not show up in sector 95, where the expected SNR was 12. The noise floor measured on the star itself in that sector is 13.5. Should the candidate be vetoed?

    ??? success "Show answer"
        Not on the basis of that sector. A floor of 13.5 means that the narrow-band search, on this star, finds peaks of SNR 13.5 in 10 % of the tries at random periods. A real signal with an expected SNR of 12 may simply not stand out. The project only counts an absence as decisive if the expected SNR is ≥ 10 **and** ≥ 1.5 times the floor (here, it would require 20), and it only vetoes with a decisive absence in at least two sectors. This is the real case of signal 1634: the decision came from the blind search in sectors 95 to 97, which recovered neither the period nor its double. The general idea: a fixed SNR limit does not work, because the search noise (median 5.2, p90 19, p99 98 in sector 69) varies a lot from star to star.

## Passing criterion

- **Comfortably done**: complete answers to at least 8 of the 10 questions, **including** questions 1 and 4. These two are production questions: what matters is the structure (hypothesis, measurement, stopping criterion; ephemeris, uncertainties, tests, limitations).
- **Almost there**: 6 or 7 complete answers. Go back to the lessons for the questions you missed and redo the worked exercises without looking at the answers.
- **Not yet**: fewer than 6. Reread lessons A3 and A5, which hold the concepts asked about most, and retake the self-assessment in two weeks.

For each question you got wrong, write down in your notebook which lesson answers it and what was missing. That record is worth more than the grade.

Once you pass, the next step is practical: review the candidate queue of a new sector carefully, document your reviews and, if a candidate survives everything, prepare the submission package from lesson A6.
