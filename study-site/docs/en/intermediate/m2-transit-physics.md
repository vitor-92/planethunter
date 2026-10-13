# M2. Transit physics

<p class="meta">Intermediate level · weeks 3–5 · about 12 hours</p>

!!! abstract "In this lesson you will learn"
    - Kepler's third law and how it links the period, the distance and the density of the star.
    - How to predict the duration of a transit, the formula used in the `duration` test.
    - What the impact parameter is and why grazing transits are V-shaped.
    - Why the bottom of the transit is rounded (limb darkening).
    - The difference between the secondary eclipse of a binary and the occultation of a planet, with the case of WASP-18 b.
    - Why a transit that is too short on a giant star points to a blend.

## Kepler's third law

In 1619, Johannes Kepler found that the farther a planet is from the Sun, the longer it takes to go around once. Newton later showed the exact formula. For a planet of negligible mass on a circular orbit of radius $a$ around a star of mass $M_\star$:

$$
P^2 = \frac{4\pi^2 a^3}{G M_\star}
$$

$G$ is the gravitational constant. In words: the square of the period is proportional to the cube of the distance.

For transits, the distance in kilometers matters less. What matters is the distance **in stellar radii**, $a/R_\star$. And here something beautiful happens. Write the mass of the star as volume times density, $M_\star = \tfrac{4}{3}\pi R_\star^3 \rho_\star$, and substitute:

$$
\left(\frac{a}{R_\star}\right)^3 = \frac{G \rho_\star P^2}{3\pi}
$$

The radius and the mass have disappeared individually. All that is left is the **mean density of the star**, $\rho_\star$. Given the period, $a/R_\star$ depends only on how compact the star is.

Two values to anchor you:

- Earth and Sun: $a/R_\star \approx 215$. The mean density of the Sun is 1.41 g/cm³.
- Since $a/R_\star \propto P^{2/3}$, a 10-day planet around the Sun has $a/R_\star = 215 \times (10/365.25)^{2/3} \approx 19.5$.

## The transit duration

Think of the planet as a car on a circular track. The track has length $2\pi a$, and the car takes the period $P$ to go around once. During the transit, it covers only the stretch that lies in front of the star's disk. In a central transit, that stretch is about $2R_\star$ long (plus the diameter of the planet itself). So:

$$
T_{14} \approx \frac{P}{2\pi a} \times 2R_\star(1+k) = \frac{P}{\pi}\,\frac{R_\star}{a}\,(1+k)
$$

where $k = R_p/R_\star$. $T_{14}$ is the total duration, from first to fourth contact (from the moment the planet first touches the disk until it has fully left it).

The exact form, used by PlanetHunter in the `predicted_duration_days` function of `vetting/basic.py`, for a circular orbit and a central transit ($b = 0$):

$$
T_{14} = \frac{P}{\pi}\,\arcsin\!\left(\frac{1+k}{a/R_\star}\right), \qquad \frac{a}{R_\star} = \left(\frac{G\rho_\star P^2}{3\pi}\right)^{1/3}
$$

Since $a/R_\star$ is usually much larger than 1, the arcsine barely changes the result. Putting it all together, the duration grows with $P^{1/3}$ and falls with $\rho_\star^{1/3}$. Large, low-density stars (giants) have long transits. Small, dense stars (red dwarfs) have short transits.

Predicted durations for a central transit on a star identical to the Sun:

| Period | 1 d | 3 d | 5 d | 10 d | 20 d | 40 d | 1 year |
|---|---|---|---|---|---|---|---|
| $T_{14}$ (b = 0) | 1.8 h | 2.6 h | 3.1 h | 3.9 h | 4.9 h | 6.2 h | 13.0 h |

!!! example "Exercise 1"
    Estimate the duration of a central transit ($b = 0$) of a planet with a 10-day period around a star identical to the Sun. Use $T_{14} \approx (P/\pi)(R_\star/a)$, ignoring the size of the planet. Then compare with the value from a real dossier.

    ??? success "Show answer"
        **Step 1: $a/R_\star$.** Scaling from the Earth: $a/R_\star = 215 \times (10/365.25)^{2/3}$. The ratio 10/365.25 = 0.0274. Raised to 2/3: 0.0908. So $a/R_\star = 215 \times 0.0908 \approx 19.5$.

        Checking with the density formula: $\rho_\odot = 1410$ kg/m³, $P = 864{,}000$ s, $G = 6.674 \times 10^{-11}$. $G\rho P^2/(3\pi) = 6.674\times10^{-11} \times 1410 \times 7.46\times10^{11} / 9.42 \approx 7{,}450$. Cube root: **19.5**. It matches.

        **Step 2: duration.** $T_{14} \approx (10/\pi) \times (1/19.5) = 3.183 / 19.5 = 0.163$ day. In hours: 0.163 × 24 ≈ **3.9 hours**.

        With an Earth-sized planet ($k \approx 0.009$), multiply by 1.009: still 3.9 h. With the exact formula (arcsine), you get 3.91 h. The approximation is excellent.

        **Comparison.** In a dossier, the vetting table shows something like "T14 3.11 h vs predicted (b=0) 3.79 h" in the `duration` row. That is the case of Pi Men c (period 6.27 d, star with 1.15 R☉ and 1.1 M☉). If the star is similar to the Sun and the period is close to 10 days, expect a predicted value close to 3.9 h, and an observed value equal to it or smaller.

!!! tip "In the tool"
    The `duration` test divides the observed duration (from the trapezoid fit) by the predicted one with $b = 0$. It passes if the ratio is between **0.15** and **1.67** (`duration_ratio_min` and `duration_ratio_max`). The mass comes from the TIC; if it is missing, it is estimated from $\log g$ and the radius. Without a stellar radius, or when the fit hits the edge of its allowed range (the duration is then not really measured), the test is marked "no data" and the score is multiplied by 0.95. Failing is a soft failure that costs a factor of 0.6 in the score. In the dossier, the **Parameters** section shows R*, M* and T14.

### Why above 1.67 is suspicious

For a circular orbit, the central transit is the **longest possible**. Any inclination shortens the chord. So a duration much longer than the one predicted with $b = 0$ tells you that some assumption failed:

- the star is larger and less dense than the TIC says (a subgiant cataloged as a dwarf);
- the signal comes from **another**, larger star in the same pixel;
- the orbit is eccentric, and the transit happens far from the point closest to the star;
- the period is wrong.

Why 1.67 and not just above 1? Because the stellar radius in the TIC has errors and an eccentric orbit can lengthen a transit (Kipping 2010). The limit 1.67 is the one used by LEO-Vetter (Kunimoto et al. 2025). The project used 1.3 before; when it measured the change, raising the limit to 1.67 failed no known planet and stopped failing dozens of new signals whose only problem was a somewhat long transit.

A real case from sector 69: TOI-724.01 showed T14 = 8.40 h against a predicted 3.56 h, a ratio of 2.36. Soft failure in `duration`.

### Why below 0.15 is suspicious: signal 1594

In the first real slice of sector 69 (2164 stars), signal **1594** reached P1 with a score of 1.0. A perfect candidate? The numbers from the dossier:

- star TIC 31273263: radius 3.06 R☉, mass 1 M☉. It is a **giant** (or subgiant): three times the radius of the Sun with the same mass;
- period 6.354 d, depth 1,091 ppm;
- observed duration: **0.58 h**;
- predicted duration with $b = 0$: **10.71 h**. Ratio: 0.054.

A giant has a very low density: $\rho = 1/3.06^3 \approx 0.035$ times that of the Sun. That is why $a/R_\star$ is small (about 4.7) and a planet takes hours to cross the enormous disk. A half-hour transit does not fit this star.

To shorten from 10.7 h to 0.58 h (a factor of 18.5) just by changing the star, the density would have to be $18.5^3 \approx 6{,}300$ times higher. Not even a red dwarf gets that far. The plausible explanations are: the signal comes from **another star**, smaller and denser, mixed into the same pixel (a **blend**), probably with a grazing eclipse; or it is an extremely grazing transit ($b \approx 0.99$) on the giant itself; or it is not a transit at all. In any case, it is not a strong candidate. There is another clue pointing the same way: the star already has cataloged objects, and the severity code (`alerts/severity.py`) cites signal 1594 as an example of a star that is a cataloged eclipsing binary, in which case a new signal is almost always an eclipse.

This signal motivated the lower limit `duration_ratio_min: 0.15`, with the comment in `config/thresholds.yaml` citing signal 1594 itself. Under the current rule, this failure multiplies the score by 0.6, and the signal is no longer P1.

!!! example "Exercise 2"
    Redo the prediction for signal 1594. Data: $P = 6.354$ d, $R_\star = 3.06$ R☉, $M_\star = 1$ M☉, $k = 0.033$. Use the scaling from the Sun: $a/R_\star = 215 \times (P/365.25)^{2/3} \times (\rho_\star/\rho_\odot)^{1/3}$.

    ??? success "Show answer"
        Relative density: $\rho_\star/\rho_\odot = M/R^3 = 1/28.65 = 0.0349$. Cube root: 0.327.

        Period: $6.354/365.25 = 0.0174$. Raised to 2/3: 0.0671.

        $a/R_\star = 215 \times 0.0671 \times 0.327 \approx 4.72$.

        $T_{14} = (P/\pi)\arcsin((1+k)/(a/R_\star)) = 2.023 \times \arcsin(1.033/4.72) = 2.023 \times \arcsin(0.219) = 2.023 \times 0.221 = 0.447$ d = **10.7 h**. Exactly the value in the dossier.

        Observed/predicted ratio: 0.58/10.7 = 0.054, below 0.15. It fails.

## Impact parameter and the V shape

The **impact parameter** $b$ tells you where the planet crosses the star's disk, measured in stellar radii from the center:

$$
b = \frac{a\cos i}{R_\star}
$$

where $i$ is the inclination of the orbit (90° = seen exactly edge-on).

- $b = 0$: the planet passes through the center. Longest chord.
- $b = 0.7$: it passes higher up, shorter chord.
- $b \approx 1$: it scrapes the edge. A **grazing** transit.

The length of the chord is proportional to $\sqrt{(1+k)^2 - b^2}$. For small planets, $T_{14} \approx T_{14}(b=0)\sqrt{1-b^2}$. This explains why the ratio in the `duration` test usually comes out below 1 for real planets.

!!! example "Exercise 3"
    In sector 1, PlanetHunter measured for Pi Men c: T14 = 3.11 h, predicted with $b = 0$: 3.79 h. Estimate the impact parameter.

    ??? success "Show answer"
        Ratio: 3.11/3.79 = 0.82. With $T_{14}/T_{14}(b=0) \approx \sqrt{1-b^2}$: $1 - b^2 = 0.82^2 = 0.672$, so $b^2 = 0.328$ and **$b \approx 0.57$**.

        This is a rough estimate: the trapezoid fit, the TIC radius and the estimated mass all have uncertainty. Check the published value for Pi Men c in the NASA Exoplanet Archive and compare.

### The ramps of the transit

A transit has four contacts. Between the 1st and the 2nd, the planet is **entering** the disk (the downward ramp, duration $\tau$). Between the 2nd and the 3rd, it is entirely in front of the star (the bottom). Between the 3rd and the 4th, it is leaving (the upward ramp).

For small planets and $b$ not too close to 1 (Winn, 2010):

$$
\frac{\tau}{T_{14}} \approx \frac{k}{1-b^2}
$$

Two things make the ramps longer:

1. **A large $k$.** A small planet enters quickly: $k = 0.016$ gives very thin ramps. A companion star with half the radius of the primary ($k = 0.5$) spends almost half the eclipse entering.
2. **$b$ close to 1.** In a grazing transit, the planet is never entirely over the disk. There is no flat bottom.

In the limit, the ramps meet in the middle and the transit becomes a **triangle**: the V shape. A box or a U suggests a planet. A V suggests a binary or a grazing transit.

!!! tip "In the tool"
    The `shape` test fits a **trapezoid** to the folded curve and measures $\tau/T_{14}$. A value of 0.5 is a perfect triangle. The current limit is **0.35** (`v_shape_max`). The same test fails if $R_p/R_\star > 0.3$ (`rp_rs_max`), the size of a star, not a planet.

    The calibration was measured in sector 69. With a limit of 0.45, the test caught **no** false positives at all. With 0.35, it catches **8 of 18** TFOPWG false positives and flags **3 of 50** planets, all of them real grazing transits: HIP 65 A b, LTT 9779 b and TOI-2382 b. That is why it started as a soft failure (weight 0.5). Since the 2026-10-10 audit it is a **hard fail**: a failure alone fails the verdict, though it is still not a veto. The measured cost is about 3 grazing planets per sector; the gain is stopping eclipsing binaries found at half their period.

    Measured values: Pi Men c 0.11; WASP-18 b 0.14; the false positives TOI-297.01 0.42, TOI-4858.01 0.41 and TOI-189.01 0.41.

## Limb darkening

Look at a photo of the Sun: the center is brighter than the edge. This is **limb darkening**. At the edge, your line of sight passes through the star's atmosphere sideways and only sees the higher layers, which are cooler and emit less light.

The consequence for the transit: when the planet is at the center of the disk, it covers the brightest region, and the dip is larger. Near the edge, it covers a darker region, and the dip is smaller. The bottom of the transit is no longer flat and becomes **rounded**, U-shaped.

This affects the depth measurement. For Pi Men c in sector 1:

| Model | Depth |
|---|---|
| Box (Lightkurve's BLS, lesson M4) | 228 ppm |
| Trapezoid (PlanetHunter vetting) | 272 ppm |
| TLS model, with limb darkening | 287 ppm |

The box averages over the whole transit, including the ramps and the shallow parts of the U. The model with limb darkening captures the deeper bottom. That is why TLS, which uses this model, is more sensitive than BLS (lesson [M3](m3-periodograms.md)).

The rounding also inflates the $\tau/T_{14}$ measured by the trapezoid a little: the fit interprets the curvature of the bottom as a ramp. That is why real planets show up with 0.1 to 0.15, and not with the geometric value of 0.02.

## Secondary eclipse and planetary occultation

On a circular orbit, half a period after the transit, the object passes **behind** the star. What you see at that moment, at **phase 0.5**, depends on how bright it is.

- **Eclipsing binary.** The companion is a star and has its own light. When it is hidden, the total brightness drops: this is the **secondary eclipse**. If the two stars are similar, the two eclipses have similar depths.
- **Planet.** The planet shines very little: reflected light and heat. When it disappears behind the star, the dip is tiny. This is called an **occultation**. For almost all planets, it is invisible to TESS.

The exception is **ultra-hot Jupiters**. WASP-18 b orbits its star in less than a day and is so hot that TESS sees its light disappear. The project's documentation records about 340 ppm at phase 0.5. In the final sector 69 run, the `secondary` test measured 276 ppm, **3% of the primary** (which is about 10,300 ppm), with a significance of 8 sigma. A real and significant dip at phase 0.5, on a confirmed planet.

On the project's first day, WASP-18 b was **vetoed as a binary**. The fix used physics: a planet's occultation is a small fraction of the transit, while a binary's secondary is usually a large fraction. The current rule vetoes only if both conditions hold together:

- a secondary above 5 sigma (`secondary_veto_sigma`), **and**
- a secondary at 10% or more of the primary's depth (`secondary_veto_ratio: 0.1`).

Between 3 and 5 sigma, or above 5 sigma but below 10%, it is a soft failure (weight 0.4).

Cases in sector 69 vetoed for a secondary: TOI-287.01 (4,503 ppm at phase 0.5, 37% of the primary), TOI-349.01 (1,376 ppm, 13%) and TOI-187.01 (108%, that is, two practically identical eclipses). All of them are TFOPWG false positives.

!!! warning "Eccentric orbits"
    If the orbit is eccentric, the secondary does not fall at phase 0.5. The `secondary_scan` test looks for the largest dip at any phase between 0.1 and 0.9, with a higher limit (5 sigma), because it looks in many places (remember the look-elsewhere effect, lesson M1). It was created because the eccentric binary TOI-367.01 passed everything.

!!! example "Exercise 4"
    Using PlanetHunter's rules, decide the result of the `secondary` test in each case:

    a) Primary of 8,000 ppm; dip at phase 0.5 of 400 ppm at 9 sigma.
    b) Primary of 3,000 ppm; dip at phase 0.5 of 600 ppm at 6 sigma.
    c) Primary of 3,000 ppm; dip at phase 0.5 of 600 ppm at 4 sigma.

    ??? success "Show answer"
        a) Ratio 400/8,000 = 5%. Significant (9 > 5 sigma), but below 10%. **Soft failure, no veto.** Compatible with the occultation of a very hot planet, like WASP-18 b.

        b) Ratio 600/3,000 = 20%, and 6 > 5 sigma. **Veto.** An eclipsing binary profile.

        c) Ratio 20%, but only 4 sigma: it goes past 3 sigma (failure) and does not reach 5 (no veto). **Soft failure.** It is worth looking at the "Odd, even and secondary" panel in the dossier and searching for the secondary in other sectors.

## Summary: from physics to the test

| Physics | Quantity | Vetting test |
|---|---|---|
| Kepler + stellar density | predicted $T_{14}$ | `duration` |
| Impact parameter, large $k$ | $\tau/T_{14}$ | `shape` |
| Depth $\approx k^2$ | $R_p$ | `radius`, `shape` ($R_p/R_\star$) |
| Luminous companion | dip at phase 0.5 | `secondary` |
| Eccentric orbit | dip at another phase | `secondary_scan` |

## Lesson checklist

- [ ] I can write Kepler's third law and explain why $a/R_\star$ depends only on the density of the star.
- [ ] I computed the duration of a 10-day transit on a star like the Sun (about 3.9 h).
- [ ] I know why a ratio above 1.67 or below 0.15 in the `duration` test is suspicious.
- [ ] I can explain the impact parameter and why grazing transits and binaries are V-shaped.
- [ ] I know why the bottom of the transit is rounded and why the box underestimates the depth.
- [ ] I know the difference between a secondary eclipse and an occultation, and the 10% rule.
- [ ] I opened a dossier and read the notes for `duration`, `shape` and `secondary` in the vetting table.

## Going further

- Winn (2010), "Transits and Occultations", free on arXiv ([arXiv:1001.2010](https://arxiv.org/abs/1001.2010)). Sections 1 to 3. It is the classic text: every formula in this lesson is there, with its derivation.
- Seager & Mallén-Ornelas (2003), *The Astrophysical Journal* 585, 1038. Shows how to get the density of the star from the shape of the transit alone; the basis of the `duration` test.
- Pi Men c's page in the NASA Exoplanet Archive ([exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu)): compare the published impact parameter with the one you estimated in exercise 3.
- This course's [transit simulator](../lab/transit-simulator.md): change the parameters and watch the shape of the curve respond.
