# M1. Statistics for signals

<p class="meta">Intermediate level · weeks 1–3 · about 15 hours</p>

!!! abstract "In this lesson you will learn"
    - Mean, median, standard deviation and MAD, and why PlanetHunter prefers the median.
    - What "3 sigma" means and why the system requires an SNR of 7.1.
    - Why the signal-to-noise ratio grows with the square root of the number of points.
    - The difference between white noise and red noise, and how the project measures red noise in blocks.
    - How the chi-squared test checks whether several transits "agree".
    - How to read the confidence interval of a recall, such as 123/135.

## Why statistics

Every TESS brightness measurement comes with an error. If you measure the same star twice, two minutes apart, the numbers will not be the same. This fluctuation is the **noise**.

A transit of Pi Men c lowers the brightness by about 300 ppm. The noise of each point for this star is about 130 ppm. In other words: at any single point, the transit is only twice as large as the normal fluctuation. Even so, the planet is detected with room to spare. Statistics explains how.

The central question of this lesson is always the same: **is this dip real, or could it be chance?**

## Mean, median and standard deviation

Imagine five normalized brightness measurements (1.0 = normal brightness), in ppm of deviation:

| Measurement | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Deviation (ppm) | −120 | +80 | +10 | −40 | +3,000 |

The fifth one is a **flare**, an explosion on the surface of the star, or a cosmic ray.

- **Mean**: the sum divided by the count. $(-120 + 80 + 10 - 40 + 3000)/5 = 586$ ppm. A single bad point dragged the mean far away from everything.
- **Median**: sort the values and take the one in the middle. Sorted: −120, −40, 10, 80, 3,000. Median = 10 ppm. The flare changes nothing.
- **Standard deviation** ($\sigma$): the typical size of the fluctuation around the mean. It is the square root of the mean of the squared differences. It is also very sensitive to extreme points.

The median is **robust**: it withstands absurd points without moving. That is why PlanetHunter uses the median to define the "normal" brightness level outside the transit.

### MAD: the robust standard deviation

The **MAD** (*median absolute deviation*) does for the standard deviation what the median does for the mean:

1. Compute the median of the data.
2. Compute the distance from each point to that median.
3. Take the median of those distances.

For normally distributed data, $\sigma \approx 1.4826 \times \text{MAD}$. This is exactly the calculation the vetting uses (function `_robust_sigma` in `vetting/basic.py`).

The MAD also decides which points to throw away during cleaning. PlanetHunter removes points **above** median + 4 × (1.4826 × MAD), the `sigma_upper: 4.0` in `config/thresholds.yaml`. It never removes points below: a transit is precisely a sequence of points below normal.

!!! example "Exercise 1"
    Compute the MAD and the robust sigma of the five measurements in the table above (−120, +80, +10, −40, +3,000 ppm). Compare with the ordinary (sample) standard deviation, which is about 1,350 ppm.

    ??? success "Show answer"
        Median = 10 ppm. Distances to 10: 130, 70, 0, 50, 2,990. Sorted: 0, 50, 70, 130, 2,990. Their median: **MAD = 70 ppm**.

        Robust sigma = 1.4826 × 70 ≈ **104 ppm**.

        The ordinary standard deviation comes out at about 1,350 ppm, thirteen times larger, because of a single point. With the robust sigma, the flare sits (3,000 − 10)/104 ≈ 29 sigmas from the median and would be removed by the 4-sigma cut.

## The normal distribution and "sigma"

When noise comes from many small independent causes, the values are distributed along a **normal curve** (or Gaussian), the famous bell. It has a useful property: the chance of a value landing far from the mean depends only on how many $\sigma$ away it is.

| Distance | Chance of pure noise going past this value (downward only) |
|---|---|
| 1 σ | 16% |
| 2 σ | 2.3% |
| 3 σ | 0.13% (1 in 740) |
| 5 σ | 0.000029% (1 in 3.5 million) |
| 7.1 σ | about 6 × 10⁻¹³ (1 in 1.6 trillion) |

Saying that a signal is "3 sigma" means: if it were only normal noise, a value like this would show up 1 time in 740.

### Why 3 sigma is not enough: the look-elsewhere effect

1 in 740 sounds rare. But the PlanetHunter search tests thousands of periods and, for each one, thousands of transit positions and durations. That is millions of tries per star, and there are about 20,000 stars per sector. With a million tries, pure noise produces about 1,350 "signals" at 3 sigma. This is called the **look-elsewhere effect**.

The **7.1 sigma** limit comes from the Kepler mission (Jenkins, Caldwell & Borucki, 2002). It was chosen so that, in a search the size of Kepler's, white Gaussian noise would produce fewer than one false alarm in total. TESS and PlanetHunter inherited this value (`snr_min: 7.1`).

!!! warning "Real noise is not normal"
    The table above holds for ideal Gaussian noise. Real noise has fatter tails. The project measured this: searching for a signal in a narrow range of periods in stars **without** a signal (144 tries), the median SNR was 5.2, but 10% of the tries went past 19 and 1% went past 98. That is why SNR ≥ 7.1 is necessary, but not sufficient. That is what vetting is for.

## SNR and the square root of N

The **signal-to-noise ratio** (SNR) compares the size of the dip with the uncertainty with which you measure it.

The key idea: **the mean of N independent points has an error of $\sigma/\sqrt{N}$**. A single measurement fluctuates by $\sigma$. The mean of 4 measurements fluctuates by $\sigma/2$. The mean of 100 measurements, by $\sigma/10$. The noise partly cancels out when you add points together, because some points go up and others go down.

In a transit, we measure the depth as the mean of the points inside the transit minus the normal level. So:

$$
\text{SNR} \approx \frac{\delta}{\sigma / \sqrt{N_\text{in transit}}} = \frac{\delta}{\sigma}\sqrt{N_\text{in transit}}
$$

where $\delta$ is the depth and $\sigma$ is the noise of one point.

### Numerical example: Pi Men c in sector 1

Numbers measured by running lesson [M4](m4-tess-data-in-python.md) with Lightkurve:

- mean depth (box model): $\delta \approx 228$ ppm. This is less than the ~300 ppm at the bottom of the transit, because the box averages in the sloped edges; lesson [M2](m2-transit-physics.md) explains this;
- noise of one 2-minute point, after flattening: $\sigma \approx 128$ ppm;
- transit duration: about 0.12 day, that is, about **86 points** of 2 minutes per transit;
- transits in the sector: **5**, a total of about 430 points in transit.

With a single transit:

$$
\text{SNR}_1 = \frac{228}{128/\sqrt{86}} = \frac{228}{13.8} \approx 16.5
$$

With all five:

$$
\text{SNR}_5 = \frac{228}{128/\sqrt{430}} = \frac{228}{6.17} \approx 37
$$

PlanetHunter measures the SNR in the same spirit, on its own flattened curve, using the real transit duration and a robust estimate of the noise (based on the median). Its value for this signal is of the same order.

Notice the consequence: **to double the SNR, you need four times as many points**, that is, four times as many transits. That is why combining sectors helps small planets so much, and why a long-period planet, with 2 transits in a sector, is hard.

!!! example "Exercise 2"
    A hypothetical star has a noise of 1,000 ppm per 2-minute point. A candidate has a depth of 500 ppm and 3-hour transits.

    a) What is the SNR of a single transit?
    b) How many transits are needed to reach SNR 7.1, assuming white noise?

    ??? success "Show answer"
        a) 3 hours = 180 minutes = 90 points of 2 minutes. Error of the mean of one transit: $1000/\sqrt{90} = 105$ ppm. SNR = 500/105 ≈ **4.7**.

        b) With $n$ transits, SNR = $4.7\sqrt{n}$. We want $4.7\sqrt{n} \geq 7.1$, so $\sqrt{n} \geq 1.51$ and $n \geq 2.3$. You need **3 transits**. With 2, the SNR stays at 6.7 and the signal is vetoed by the `snr` gate.

## White noise and red noise

The $\sqrt{N}$ only works if each point fluctuates **independently** of its neighbor. This is **white noise**: think of drizzle falling, each drop landing in a random place.

In practice, there are also fluctuations that last for hours: the star pulsates, a spot rotates, the telescope wobbles a little, the detrending leaves leftovers. Neighboring points go up and down together. This is **red noise** (or correlated noise). Think of waves in the sea: there is no point averaging ten measurements in a row if all ten are on the same crest.

With red noise, the mean of N neighboring points does **not** fall as $\sigma/\sqrt{N}$. It stops falling at a certain floor. And a 2-hour ripple of 200 ppm looks a lot like a transit.

### How to measure it: the block method of Pont et al. (2006)

Pont, Zucker & Queloz (2006) proposed a simple model:

$$
\sigma_N^2 = \frac{\sigma_w^2}{N} + \sigma_r^2
$$

The first term is the white noise, which shrinks with N. The second, $\sigma_r$, is the red noise, which does **not** shrink. For large N, it dominates.

The practical way to measure it is empirical:

1. Take the light curve **outside** the transits.
2. Cut it into blocks of N consecutive points (N = the number of points in one transit).
3. Compute the mean of each block.
4. Measure the standard deviation of those means.

If the noise were white, this deviation would be $\sigma/\sqrt{N}$. If it comes out larger, there is red noise, and that larger value is the one you should use as the error.

!!! tip "In the tool"
    The `BlockNoise` class in `src/planethunter/vetting/basic.py` does exactly this. The error of the mean of N points is the **larger** of $\sigma/\sqrt{N}$ (with a robust $\sigma$, via the MAD) and the standard deviation of the means of blocks of N points, measured outside the transit. It is used in the `odd_even`, `secondary`, `secondary_scan` and `consistency` tests.

    The reason was measured in sector 69: with the naive error $\sigma/\sqrt{N}$, **4 of 41 confirmed planets** failed the transit-to-transit consistency test. The error was too small, and normal differences looked significant.

    The same idea also gives a detection measure, the **S/N_pink** ("pink" because it mixes white and red noise). It is the SNR computed with the error from the formula above, using $\sigma_r$ measured in blocks the length of the transit. It is always smaller than or equal to the plain SNR, and much smaller when the star has slow wiggles lasting hours. The TESS quick-look pipeline (QLP) requires S/N_pink ≥ 9; in PlanetHunter, a signal below 9 gets a soft failure in the `snr_pink` test (lesson [M5](m5-vetting-in-practice.md)).

    There is a second indicator during cleaning: the ratio between the spread of the curve and the point-to-point noise (`red_noise_ratio` in `preprocess/clean.py`), both measured with the MAD so that a deep transit does not inflate it. For white noise it is about 1. Above 1.2, the system redoes the detrending with smaller windows. The star of TOI 862.01 went well past that limit with the default window. See lesson [M3](m3-periodograms.md).

!!! example "Exercise 3"
    Outside the transit, a curve has a robust sigma of 600 ppm per point. A transit has 36 points. You cut the curve into blocks of 36 points and the standard deviation of the block means comes out at 220 ppm.

    a) What would the error of the mean of 36 points be if the noise were white?
    b) Which error does `BlockNoise` use?
    c) A single 500 ppm transit: what is the SNR in each case?

    ??? success "Show answer"
        a) $600/\sqrt{36} = 600/6 = 100$ ppm.

        b) The larger of 100 and 220: **220 ppm**. There is strong red noise; the blocks fluctuate more than twice as much as expected.

        c) White noise: 500/100 = 5.0. With blocks: 500/220 ≈ 2.3. The naive calculation would make the transit look twice as reliable as it is.

## Chi-squared: do the transits agree with each other?

A real planet produces identical transits every orbit. If one of the transits is much deeper than the others, something is wrong: an instrumental event, an inverted flare, or two phenomena mixed together.

How do you decide whether the differences are "normal"? With the **chi-squared test** ($\chi^2$):

1. Measure the depth of each transit, $d_i$, and the error of each one, $\sigma_i$ (this is where `BlockNoise` comes in).
2. Compute the weighted mean $\bar d$ (transits with smaller errors weigh more).
3. Add up the squared deviations, in units of error:

$$
\chi^2 = \sum_i \left(\frac{d_i - \bar d}{\sigma_i}\right)^2
$$

If the differences are only noise, each term is about 1 on average, and $\chi^2$ stays close to the number of **degrees of freedom**: the number of transits minus 1. If it comes out much larger, the transits do not agree.

The **p-value** translates $\chi^2$ into a probability: the chance that noise alone produces a disagreement this large or larger. PlanetHunter fails the test if p < 0.001 (`transit_consistency_pvalue_min`).

The test has a second criterion: with 3 or more transits, it fails if a single transit accounts for more than 80% of the total SNR². This is the "one strange event dominating" case.

!!! example "Exercise 4"
    Five transits with depths of 290, 270, 310, 280 and 300 ppm, all with an error of 25 ppm.

    a) Compute $\chi^2$ and say whether it passes the test.
    b) Replace the last one with 600 ppm. What happens?

    Given: with 4 degrees of freedom, p = 0.001 corresponds to $\chi^2 \approx 18.5$.

    ??? success "Show answer"
        a) Mean (equal weights) = 290 ppm. Deviations: 0, −20, +20, −10, +10. In units of error: 0; −0.8; 0.8; −0.4; 0.4. Squares: 0; 0.64; 0.64; 0.16; 0.16. **$\chi^2 = 1.6$**, well below 18.5. The p-value is about 0.81. **It passes.**

        b) Mean = 350 ppm. Deviations: −60, −80, −40, −70, +250. In errors: −2.4; −3.2; −1.6; −2.8; 10. Squares: 5.76; 10.24; 2.56; 7.84; 100. **$\chi^2 \approx 126$**, p-value of the order of $10^{-26}$. **It fails.** A single disagreeing transit is enough.

!!! warning "Pitfall: very strong signals"
    When the SNR is huge, the error of each transit becomes tiny, and real but harmless differences (a detrending residual, a transit cut by a gap) turn into dozens of sigmas. In sector 69, high-SNR confirmed planets failed `consistency`: WASP-97 b (p ≈ $10^{-35}$), WASP-18 b (p ≈ $10^{-26}$), TOI-481 b. That is why this test is a **soft failure** (it multiplies the score by 0.5), not a veto.

!!! tip "In the tool"
    In the dossier, the **"Depth per transit"** section is the chi-squared in plot form: one point per transit, with an error bar, and a dashed line at the mean. Good signal: points lined up on the line. Bad signal: one point far away from the others. In the vetting table, the `consistency` row shows the number of transits, the p-value and the fraction of the SNR² in the largest transit.

## Binomial confidence interval: how much to trust a recall

The project's benchmark measures the **recall**: of 135 TOIs that should be detectable in sector 69, how many the system finds. Result: **123 of 135 = 91.1%**.

But 135 is a small sample. If you toss a biased coin 135 times, the fraction of heads varies from one round to the next. The same holds here. The right question is: what range of "true" recall is compatible with 123/135?

A rough calculation: the error of a proportion $p$ measured over $n$ cases is

$$
\text{SE} = \sqrt{\frac{p(1-p)}{n}} = \sqrt{\frac{0.911 \times 0.089}{135}} \approx 0.0245
$$

that is, 2.45 percentage points. The 95% interval is about ±1.96 SE: from 86.3% to 95.9%.

The project's report uses a better formula, the **Wilson interval**, which does not let the range go past 100% and becomes asymmetric near the edges. Result: **85.1% to 94.8%**. In plain language: the system's true recall, on this type of target, is very likely between 85% and 95%.

Practical consequence: a change that takes the recall from 120/135 (88.9%) to 123/135 (91.1%) is **compatible with chance**. Three more TOIs do not prove an improvement on their own. You need to look at which TOIs changed and why, as the history report does.

!!! example "Exercise 5"
    Using the simple approximation, compute the 95% interval for the first benchmark run: 114 of 135 (84.4%). Does it overlap with the interval of the final run (85.1% to 94.8%)?

    ??? success "Show answer"
        $p = 0.844$. SE = $\sqrt{0.844 \times 0.156 / 135} = \sqrt{0.000975} \approx 0.0312$. Interval: 0.844 ± 1.96 × 0.0312 = 0.844 ± 0.061, that is, **78.3% to 90.5%**.

        Yes, it overlaps (from 85.1% to 90.5%). Even so, the improvement from 114 to 123 is more convincing than the numbers alone suggest, because the report shows the **cause** of each recovered TOI (stellar limits, window, alias). Statistics and diagnosis go hand in hand.

## Lesson checklist

- [ ] I can compute the mean, median, standard deviation and MAD by hand for a few numbers.
- [ ] I can explain why PlanetHunter uses the median and the MAD during cleaning.
- [ ] I know what "3 sigma" means and why the system's limit is 7.1.
- [ ] I can compute the SNR of a transit from the depth, the noise per point and the number of points.
- [ ] I can explain red noise with an analogy and describe the block method.
- [ ] I can compute a simple chi-squared and interpret the p-value.
- [ ] I can explain why a 91% recall with 135 objects could be anything between 85% and 95%.
- [ ] I opened a dossier, found the "Depth per transit" section and the `consistency` row of the vetting table.

## Going further

- Khan Academy, statistics and probability track ([www.khanacademy.org](https://www.khanacademy.org/math/statistics-probability)): descriptive statistics and the normal distribution. Do it first if mean and standard deviation still feel strange.
- Pont, Zucker & Queloz (2006), *Monthly Notices of the Royal Astronomical Society* 373, 231. The paper that formalized red noise in transits. Read the introduction and the figures.
- Jenkins, Caldwell & Borucki (2002), *The Astrophysical Journal* 564, 495. Where Kepler's 7.1 sigma limit, inherited by TESS, comes from.
- Wilson (1927), *Journal of the American Statistical Association* 22, 209. The origin of the interval used in the benchmark reports; short and readable.
- In the PlanetHunter repository, `docs/benchmarks/2026-10-09-s0069-history.md`: the recall of each run with its 95% interval. Good practice for reading proportions with uncertainty.
