# B2. The transit method

<p class="meta">Basic level · weeks 2–3 · about 4 hours</p>

!!! abstract "In this lesson you will learn"
    - Why a star's light drops when a planet passes in front of it.
    - The main rule: depth ≈ (planet radius / star radius)².
    - What period, duration and depth tell you about the system.
    - Why only a small fraction of planets transit, and how to calculate that fraction.
    - What a light curve is and how a dip is measured in ppm.

## The geometry of a transit

Go back to the flashlight and the fly from lesson B1. The fly blocks a share of the light proportional to its **area** compared with the area of the flashlight. Stars work the same way: seen from here, the star is a bright disk and the planet is a much smaller dark disk that crosses it.

```
  seen from the side (orbit edge-on)        seen from here (what the telescope "sees")

   star           planet                           .-""""-.
   (  O  )  ------- o ------->  us               /          \
                                                |     ●      |   ● = dark disk
   the planet passes between the star and us    |            |       of the planet
                                                 \          /
                                                   '-....-'
```

The area of a disk is $\pi R^2$. The fraction of light blocked is the ratio between the two areas:

$$ \delta \approx \frac{\pi R_p^2}{\pi R_\star^2} = \left(\frac{R_p}{R_\star}\right)^2 $$

Here $\delta$ (the Greek letter "delta") is the transit **depth**, $R_p$ is the planet's radius and $R_\star$ is the star's radius. The $\pi$ cancels out. All that is left is the ratio of the radii, squared.

The square is the most important detail of this lesson. Double the planet's radius and the depth quadruples. Cut the star's radius in half and the depth also quadruples.

!!! note "Why \"approximately\""
    The rule assumes the star shines equally across its whole disk. In reality, the edge of a star is a bit darker than its center (**limb darkening**, the topic of lesson M2). This rounds the bottom of the transit and changes the depth by a few percent. For building intuition, the rule is enough.

## Depth in ppm

The dips are tiny. That is why the field uses **ppm**, parts per million:

| Fraction | Percentage | ppm |
|---|---|---|
| 0.01 | 1% | 10,000 ppm |
| 0.001 | 0.1% | 1,000 ppm |
| 0.0001 | 0.01% | 100 ppm |

To convert a fraction to ppm, multiply by one million. To convert a percentage to ppm, multiply by 10,000.

With the rule and the radii from lesson B1, you get the table that appears in the project's beginner's guide:

| Planet in front of a star identical to the Sun | $R_p/R_\star$ | Depth |
|---|---|---|
| Earth | 0.0092 | about 84 ppm (0.0084%) |
| Neptune | 0.035 | about 1,250 ppm (0.13%) |
| Jupiter | 0.100 | about 10,000 ppm (1%) |

An Earth in front of the Sun blocks 84 millionths of its light. It is like noticing that a 100-watt light bulb has turned into a 99.99-watt bulb.

You can also use the rule backward. If you measured the depth and know the star's radius:

$$ R_p \approx R_\star \sqrt{\delta} $$

This is how PlanetHunter estimates the planet's radius for each signal.

## Period, duration and depth

A transit has three main numbers. Each one tells you something different.

| Number | Symbol | Unit in the project | What it tells you |
|---|---|---|---|
| Period | $P$ | days | how long the planet takes to go once around its star; from it, through Kepler's third law, the distance to the star |
| Duration | $T_{14}$ | hours | how long the planet takes to cross the disk; it depends on the size of the star and the speed of the planet |
| Depth | $\delta$ | ppm | the size of the planet compared with the star |

The **period** is the time between two consecutive transits. With the period and the time of one transit (called $T_0$), you can predict every future transit. This pair of numbers is called the **ephemeris**.

The period also gives you the distance. **Kepler's third law** says that larger orbits take longer. For a star with the Sun's mass, measuring the period in years and the distance $a$ in AU:

$$ a^3 = P^2 $$

Earth: $P = 1$ year, $a = 1$ AU. A 10-day planet ($P = 0.0274$ year) sits about 0.09 AU from its star, four times closer than Mercury.

The **duration** depends on how much path the planet travels in front of the disk and on its speed. For a transit that crosses the center of the disk, in a circular orbit, a good approximation is:

$$ T_{14} \approx \frac{P}{\pi}\,\frac{R_\star}{a} $$

For Earth: $P = 8{,}766$ hours, $R_\star / a = 696{,}000 / 149{,}600{,}000 = 0.00465$. So $T_{14} \approx 8{,}766 / 3.14 \times 0.00465 \approx 13$ hours. A distant observer would see Earth take about 13 hours to cross the Sun, once a year.

If the planet passes near the edge of the disk instead of through the center, the transit becomes shorter and more pointed. This is measured by the **impact parameter** $b$ (0 = center, 1 = edge), and you will play with it in the simulator.

## Why only a fraction of planets transit

For a transit to happen, the orbit has to be almost edge-on as seen from here. If it is tilted, the planet passes "above" or "below" the star, and nothing happens to the brightness.

Think of a lamp in the middle of a room and an ant walking in a circle around it. Only someone looking from the right height sees the ant pass in front of the lamp. The larger the circle, the narrower that band of heights becomes.

The probability that an orbit, randomly oriented, produces transits is approximately:

$$ p_{\text{transit}} \approx \frac{R_\star}{a} $$

For Earth and the Sun: $p \approx 696{,}000 / 149{,}600{,}000 \approx 0.0047$, that is, about **0.5%**. Out of every 200 systems with an Earth twin 1 AU from a Sun, only one would be aligned to show transits.

For a 10-day planet around a Sun-like star ($a \approx 0.09$ AU), the chance rises to about 5%. For a 3-day hot Jupiter ($a \approx 0.04$ AU), more than 10%. That is why transit searches mostly find short-period planets: they transit more often **and** are more likely to transit at all.

!!! warning "Common pitfall"
    "I saw no transit, so the star has no planet" is wrong. The absence of a transit almost always just means that the orbit is not aligned with us. The vast majority of planets in the galaxy will never transit for us.

## The light curve

A **light curve** is a graph of a star's brightness over time. It is the raw data behind everything in this course. The horizontal axis shows time (for TESS, in **BTJD** days, explained in lesson B3). The vertical axis shows brightness divided by the average brightness, so that "normal" equals 1.000.

```
brightness
  1.000 ─────────╮      ╭──────────────────╮      ╭─────────
                 │      │                  │      │
  0.999          ╰──────╯                  ╰──────╯
                 ↑ transit                 ↑ transit
                 |←──────── period ───────→|
                                                       time →
```

A planet transit has a characteristic shape:

1. **Entry** (ingress): the brightness drops as the planet's disk moves in front of the star.
2. **Bottom**: the whole planet is in front of the disk; the brightness stays almost constant, slightly rounded by limb darkening. The shape looks like a **U**.
3. **Exit** (egress): the brightness returns to normal.

In practice, the points of the curve do not sit on a clean line. Every measurement has **noise**: small random fluctuations. An 84 ppm transit on a star whose noise per measurement is 700 ppm is invisible to the eye. The way out is to **combine many transits**: the pipeline stacks all of them, lined up by the period (this is called **folding** the curve). The random noise partly cancels out, while the transit, which is always in the same place, adds up.

How much the transit stands out from the noise is measured by the **signal-to-noise ratio**, the **SNR**. You will study it in depth at the intermediate level. For now, remember: more transits, a brighter star and a larger planet all increase the SNR.

!!! tip "In the tool"
    The three transit numbers are columns in the candidate list (`uv run planethunter candidates`): `period_d` (period in days), `t14_h` (duration in hours) and `depth_ppm` (depth in ppm). The `rp_rearth` column is the radius estimated with $R_p = R_\star\sqrt{\delta}$. In the dossier, the **Folded transit** plot shows all transits stacked on top of each other: a clear "U" is a good sign. PlanetHunter requires at least **2 transits** (test `n_transits`) and an SNR of at least **7.1** (test `snr`) to move a signal forward. These limits live in `config/thresholds.yaml`.

!!! question "Try it in the simulator"
    Open the [transit simulator](../lab/transit-simulator.md) and **try changing the planet's radius**. Double the radius and check that the depth quadruples. Then swap the Sun for a 0.2 R☉ red dwarf while keeping the Earth. Finally, move the impact parameter close to 1 and watch the transit turn into a "V".

!!! example "Exercise 1 (from the study plan)"
    Radii: Sun 696,000 km, Earth 6,371 km, Neptune 24,622 km, Jupiter 69,911 km.

    a) Calculate the transit depth of Earth, Neptune and Jupiter in front of the Sun, in ppm.

    b) Repeat for a red dwarf with a radius of 0.2 R☉.

    c) Why is it easier to find small planets around small stars?

    ??? success "Show answer"
        **a) Sun ($R_\star$ = 696,000 km).** Use $\delta = (R_p/R_\star)^2$ and multiply by $10^6$.

        - Earth: $6{,}371 / 696{,}000 = 0.009154$. Squared: $0.0000838$. In ppm: **about 84 ppm**.
        - Neptune: $24{,}622 / 696{,}000 = 0.03538$. Squared: $0.001251$. In ppm: **about 1,250 ppm** (the guide rounds it to 1,300; 0.13%).
        - Jupiter: $69{,}911 / 696{,}000 = 0.1004$. Squared: $0.01009$. In ppm: **about 10,100 ppm**, or 1%.

        **b) Red dwarf ($R_\star = 0.2 \times 696{,}000 = 139{,}200$ km).**

        - Earth: $6{,}371 / 139{,}200 = 0.04577$. Squared: $0.002095$. **About 2,100 ppm** (0.2%).
        - Neptune: $24{,}622 / 139{,}200 = 0.1769$. Squared: $0.03129$. **About 31,000 ppm** (3.1%).
        - Jupiter: $69{,}911 / 139{,}200 = 0.5022$. Squared: $0.2522$. **About 252,000 ppm** (25%).

        Shortcut: the star has 1/5 of the Sun's radius, so every depth becomes $5^2 = 25$ times larger.

        **c)** The depth grows with the inverse square of the star's radius. The same Earth that barely shows up against the Sun (84 ppm, below the noise of a single TESS measurement for most stars) produces 2,100 ppm on a 0.2 R☉ dwarf, an easily detectable dip. Notice Jupiter too: a 25% dip is so deep that it would look like an eclipse between two stars. A very large depth is a reason to be suspicious, as you will see in lesson B4.

!!! example "Exercise 2"
    a) What is the probability that an Earth 1 AU from a star identical to the Sun transits for us?

    b) If you observed 10,000 stars identical to the Sun, each with an Earth twin, how many would show transits?

    c) What if each one had a 3-day planet (a ≈ 0.04 AU)?

    ??? success "Show answer"
        a) $p \approx R_\star / a = 696{,}000 \text{ km} / 149{,}600{,}000 \text{ km} \approx 0.0047$, that is, about **0.5%**.

        b) $10{,}000 \times 0.0047 \approx$ **47 stars**. The other 9,953 have the planet, but its orbit is not aligned with us.

        c) $a = 0.04 \times 149{,}600{,}000 \approx 5{,}984{,}000$ km. $p \approx 696{,}000 / 5{,}984{,}000 \approx 0.116$, about **12%**: close to **1,160 stars**. Small orbits are much more likely to transit.

!!! example "Exercise 3"
    The planet Pi Men c, which you will see in PlanetHunter in lesson B5, has a period of 6.27 days and a depth of about 300 ppm. The star Pi Mensae has a radius of about 1.1 R☉.

    a) Estimate the planet's radius in R⊕.

    b) How many transits fit in one TESS sector, which lasts about 27 days?

    ??? success "Show answer"
        a) $\delta = 300 \text{ ppm} = 0.0003$. $\sqrt{0.0003} \approx 0.0173$. This is $R_p/R_\star$. So $R_p \approx 0.0173 \times 1.1 \text{ R☉} \approx 0.019$ R☉. Converting with 1 R☉ ≈ 109 R⊕: $0.019 \times 109 \approx$ **2.1 R⊕**. A super-Earth or mini-Neptune, with about twice Earth's radius.

        b) $27 / 6.27 \approx 4.3$. **4 transits** fit, sometimes 5 depending on where the first one fell. In practice there may be fewer: TESS has a pause of about one day in the middle of each sector to send data to Earth (lesson B3), and a transit can fall into it.

## Lesson checklist

- [ ] I can explain why the light drops during a transit (the planet's disk blocks part of the star's disk).
- [ ] I can use $\delta \approx (R_p/R_\star)^2$ in both directions: from radius to depth and from depth to radius.
- [ ] I can convert between fraction, percentage and ppm.
- [ ] I know what each of the three numbers (period, duration, depth) tells you about the system.
- [ ] I know what an ephemeris is ($P$ and $T_0$).
- [ ] I can calculate the transit probability $R_\star/a$ and explain why it favors short orbits.
- [ ] I can describe the parts of a transit in a light curve (entry, U-shaped bottom, exit).
- [ ] I played with the simulator, changing the planet's radius, the star's radius and the impact parameter.
- [ ] I did all three exercises without looking at the answers.

## Going further

- Winn (2010), "Transits and Occultations", free on arXiv (arXiv:1001.2010). The classic text on the physics of transits. At this level, read only the introduction and look at the figures; come back to it in lesson M2.
- NASA Science, page on the transit method (science.nasa.gov/exoplanets). It has short animations showing the light curve forming as the planet passes.
- This course's [transit simulator](../lab/transit-simulator.md). Do both challenges on the page.
- Charbonneau et al. (2000), "Detection of planetary transits across a Sun-like star", *The Astrophysical Journal* 529, L45. The first exoplanet transit ever observed (HD 209458 b). Look at the light curve figure: it is the same "U" as in this lesson.
