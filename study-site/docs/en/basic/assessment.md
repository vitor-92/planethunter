# Basic level self-assessment

<p class="meta">Basic level · end of week 6 · about 1 hour</p>

!!! abstract "How to do it"
    - Answer **without looking at** the lessons. Write your answers in your notebook, in your own words and with the calculations.
    - Only then open "Show answer" and compare. Count an answer as correct if it has the main idea, even in different words.
    - Questions 1 to 6 are the ones from the study plan and decide whether you pass. Questions 7 to 10 are extras, so you can test whether your foundation is solid.

!!! warning "Passing criterion"
    Did you get **at least 5 of the 6 main questions** (1 to 6) right? Move on to the [intermediate level](../intermediate/index.md).

    Missed two or more? Go back to the lessons pointed out in each answer, let a few days pass and take the self-assessment again.

## Main questions

!!! example "Question 1"
    A planet with half the radius of Jupiter transits a star like the Sun. What is the approximate depth, in ppm?

    ??? success "Show answer"
        Use $\delta \approx (R_p/R_\star)^2$.

        Jupiter is about 0.1 R☉ (69,911 km / 696,000 km ≈ 0.100). Half of that is 0.05 R☉. So:

        $$ \delta \approx (0.05)^2 = 0.0025 $$

        Multiplying by one million: **about 2,500 ppm** (0.25%).

        Shortcut: Jupiter gives about 10,000 ppm. Half the radius gives a quarter of the depth, because the depth depends on the **square** of the ratio of the radii: $10{,}000 / 4 = 2{,}500$ ppm.

        If you answered 5,000 ppm, you forgot the square. Review [lesson B2](b2-transit-method.md).

!!! example "Question 2"
    Why are three evenly spaced transits more convincing than a single one?

    ??? success "Show answer"
        Three reasons:

        1. **Periodicity.** An orbit repeats with clockwork regularity. An isolated event could be almost anything: a telescope adjustment, a ramp at the edge of the data, a cosmic ray, an instrumental jump. Three identical, evenly spaced dips are very hard to produce by chance.
        2. **Period and prediction.** With a single transit, you don't know the period, and without the period you can't predict the next transit or calculate the planet's distance from the star. With two or more, you have the **ephemeris** (period and time of transit), which can be tested against other data.
        3. **Possible tests and a stronger signal.** With several transits you can compare odd with even, check that they all have the same depth and add them all together in the folded transit, which increases the SNR.

        In the tool, the `n_transits` test **vetoes** signals with fewer than 2 transits. Review lessons [B2](b2-transit-method.md) and [B4](b4-false-positives.md).

!!! example "Question 3"
    What does Tmag 6 mean compared with Tmag 13?

    ??? success "Show answer"
        Tmag is the star's brightness on the TESS magnitude scale. The scale is **inverted**: a smaller number means a brighter star. So the Tmag 6 star is much brighter than the Tmag 13 star.

        How much brighter? The scale is multiplicative: 5 magnitudes equal a factor of 100. A difference of 7 magnitudes gives $2.512^7 \approx 630$. The Tmag 6 star is **about 630 times brighter**.

        Why it matters: more light means less relative noise, so shallow transits become detectable. And bright stars make confirmation with other telescopes much easier. Review [lesson B3](b3-tess-telescope.md).

!!! example "Question 4"
    Name two differences between the light curve of an eclipsing binary and that of a planet.

    ??? success "Show answer"
        Any two of these:

        - **Shape.** A planet makes a transit with an almost flat bottom (U). A grazing binary makes a pointed eclipse (V).
        - **Odd and even.** A planet makes every transit the same. A binary, when the algorithm finds half the true period, shows alternating transits with different depths.
        - **Secondary eclipse.** A binary shows a second dip at phase 0.5, when the companion passes behind the main star. An ordinary planet shows nothing there (very hot planets show a small occultation, less than 10% of the transit).
        - **Depth and radius.** Binaries usually produce very deep dips; the calculated "planet" comes out too large, the size of a star.

        In PlanetHunter: the `shape`, `odd_even`, `secondary` and `radius` tests. Review [lesson B4](b4-false-positives.md).

!!! example "Question 5"
    Why can a signal come from a star that is not the target?

    ??? success "Show answer"
        Because each TESS pixel covers **21 arcseconds** of sky, a large area where several stars fit, and each star's light also spreads into neighboring pixels. The "target's" brightness is really the sum of the light from all the stars in that region.

        If a fainter neighbor star is an eclipsing binary, its eclipses show up **diluted** in the total light and can imitate a planet's shallow transit on the target. Example: a binary that contributes 1% of the light and has 50% eclipses produces a dip of 0.5%, or 5,000 ppm.

        How to investigate: the centroid test (does the center of light shift during the transit?), the difference image (where did the light go missing?) and the Gaia list of neighbors. Review lessons [B3](b3-tess-telescope.md) and [B4](b4-false-positives.md).

!!! example "Question 6"
    What is the difference between a TOI and a confirmed planet?

    ??? success "Show answer"
        A **TOI** (*TESS Object of Interest*) is a **candidate**: a signal in TESS data that the mission team examined and considered promising. It can still be a false positive. Many TOIs end up flagged by the TFOPWG as FP (false positive) or FA (false alarm).

        A **confirmed planet** has evidence independent of the transit, obtained with other telescopes, usually its mass measured by radial velocity. In the TFOPWG list, it shows up as CP (confirmed) or KP (already known).

        Between the two sits the **validated planet**: statistically very unlikely to be a false positive, backed by high-resolution images, but without a measured mass.

        The full ladder: signal → candidate → CTOI → TOI → validated → confirmed. Review [lesson B3](b3-tess-telescope.md).

## Extra questions

!!! example "Question 7"
    What is the approximate probability that an Earth at 1 AU from a Sun transits as seen from here? What does that say about stars that show no transit?

    ??? success "Show answer"
        $p \approx R_\star / a = 696{,}000 / 149{,}600{,}000 \approx 0.0047$, about **0.5%**: one in 200.

        Consequence: the absence of a transit almost never means the absence of a planet. In the vast majority of cases, the orbit simply isn't lined up with us. And transit searches favor short-period planets, which transit with a higher probability. Review [lesson B2](b2-transit-method.md).

!!! example "Question 8"
    Why is a 2 R⊕ planet much easier to find around a 0.3 R☉ red dwarf than around a 1 R☉ star?

    ??? success "Show answer"
        Because the depth is $(R_p/R_\star)^2$. Around the 1 R☉ star (109 R⊕): $(2/109)^2 \approx 0.00034$, about **340 ppm**. Around the 0.3 R☉ dwarf (about 33 R⊕): $(2/33)^2 \approx 0.0037$, about **3,700 ppm**, eleven times more.

        The factor is $(1/0.3)^2 \approx 11$. With the same noise, a dip 11 times larger has an SNR 11 times larger. On top of that, planets in the habitable zone of red dwarfs have short periods, so they transit more times per sector. Review [lesson B2](b2-transit-method.md) and play with the [simulator](../lab/transit-simulator.md).

!!! example "Question 9"
    A clean signal that passed every basic test shows up in a single sector of a star observed in 10 sectors. It doesn't show up in the other 9. What do you conclude, and which real case from sector 69 is similar?

    ??? success "Show answer"
        It is almost certainly a **glitch in that sector** (a systematic), not a planet. A planet always transits: if the signal were real, it would show up in the other sectors with comparable strength.

        This is the case of **HD 271883**: a 6.61-day, 4,900 ppm signal, perfect in basic vetting, but which did not reappear with the expected strength (expected SNR of 45 to 64) in sectors 67, 68 and 97. The `other_sectors` test, part of deep vetting, solved it. Review [lesson B4](b4-false-positives.md).

!!! example "Question 10"
    A signal shows a small dip at phase 0.5, about 3% of the depth of the main transit. Does that prove it is an eclipsing binary?

    ??? success "Show answer"
        **No.** Very hot giant planets glow enough for TESS to see their light disappear when they pass behind the star. That is an **occultation**, and it produces a small dip at phase 0.5. This is what happened with **WASP-18 b** (about 340 ppm), which PlanetHunter used to fail as a binary until the rule changed.

        The current rule only vetoes if the secondary is at least **10%** of the main one. At 3%, the signal is not vetoed by this test. Companion stars, which give off a lot of light, produce large secondaries. Review [lesson B4](b4-false-positives.md).

## Next step

Passed? Congratulations: you now know what we are looking for and why it is hard. The [intermediate level](../intermediate/index.md) explains **how** the tool decides: signal statistics, transit physics with a bit more math, periodograms, Python with real data and vetting in practice.

Before starting the intermediate level, if you haven't yet, start lesson P1 of the [programming track](../programming/index.md). It becomes required from lesson M4 on.
