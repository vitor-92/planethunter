# B4. Why almost every signal is false

<p class="meta">Basic level · week 5 · about 4 hours</p>

!!! abstract "In this lesson you will learn"
    - What an eclipsing binary is and the three marks that give it away: V shape, different odd and even eclipses, secondary eclipse.
    - How a neighbor star in the same pixel produces a fake transit on the target.
    - Which telescope glitches imitate transits: momentum dumps, orbit edges, scattered light.
    - How the star's own variability gets in the way.
    - Three real stories from sector 69 and how much PlanetHunter's vetting manages to knock down.

## The size of the problem

A periodic dip in brightness does **not** prove that a planet exists. In PlanetHunter's first real analysis, with 2,164 stars from sector 69, the funnel looked like this:

| Stage | Signals |
|---|---|
| Periodic dips found (SDE ≥ 7) | 887 |
| No match in any catalog (class `NEW`) | 648 |
| Passed basic vetting | 11 |
| Strong candidates (P1) after deep vetting | **0** |

Out of 887 signals, none survived as a strong candidate. That is not a flaw: it is what you should expect. TESS and the community have combed through this data many times, and the vast majority of dips nobody has cataloged are noise or impostors. The real work is not finding dips. It is **ruling out** everything that is not a planet.

The technical name for a signal that looks like a planet but isn't: **false positive**. The battery of tests that tries to knock them down is called **vetting** (from *to vet*, to examine carefully). Let's look at the most common impostors.

## Eclipsing binaries

An **eclipsing binary** (EB) is a pair of stars orbiting each other, with the orbit lined up with our line of sight. One passes in front of the other, and the total brightness drops. It is the most common false positive.

If the two stars are of similar size, the eclipse is deep, tens of percent, and nobody mistakes it for a planet. The danger lies in the cases where the dip is shallow. That happens when the eclipse is **grazing** (one star only skims the edge of the other) or when the star passing in front is very small. Three marks give the binary away.

### Mark 1: V shape

In a planet transit, the small disk moves fully in front of the star, and the bottom stays almost flat: a **U** shape. In a grazing eclipse between stars, the covered area grows to a maximum and immediately starts shrinking again, with no flat bottom: a **V** shape.

```
   planet (U)                 grazing binary (V)
  ───╮       ╭───            ───╮       ╭───
     ╰───────╯                   ╲     ╱
                                  ╲   ╱
                                   ╲ ╱
```

Careful: planets that cross near the edge of the star also make a V. That is why the shape, on its own, is a clue, not proof.

### Mark 2: different odd and even eclipses

In a binary, there are two eclipses per orbit: star A in front of B, and then B in front of A. If the stars are different, the two eclipses have different depths. The search algorithm, looking for identical dips, sometimes merges the two and returns **half the true period**. Then the "odd" transits (1st, 3rd, 5th...) are of one kind and the "even" ones (2nd, 4th, 6th...) of another.

```
brightness
  ───╮   ╭───╮ ╭───╮   ╭───╮ ╭───
     │   │   ╰─╯   │   │   ╰─╯        odd ones deep, even ones shallow
     ╰───╯         ╰───╯              -> it is a binary with period 2P
      1st   2nd     3rd   4th
```

A planet makes every transit with the same depth.

### Mark 3: secondary eclipse

The companion star also shines. When it passes **behind** the main star, its light disappears for a while, and the total brightness drops again, usually by less. In a circular orbit, this happens exactly halfway between two main eclipses: at **phase 0.5**.

An ordinary planet emits almost no visible light of its own, so it produces no measurable secondary. There are exceptions, and one of them is one of the stories in this chapter.

| Feature | Planet | Eclipsing binary |
|---|---|---|
| Shape | U (flat bottom) | V, when grazing |
| Odd and even | same depth | may differ |
| Phase 0.5 | flat (or a very small dip) | secondary eclipse |
| Depth | usually below 2% | often above |
| Calculated radius | up to ~2 Jupiter radii | too large for a planet |

## Background binaries and contamination

Remember lesson B3: each TESS pixel covers 21″, and several stars fit inside it. Picture the bright target and, behind it, almost in the same direction, a faint eclipsing binary. The binary has deep eclipses, but it contributes only a small fraction of the pixel's total light. Its eclipse shows up **diluted**, shallow, looking like a planet transit on the target.

$$ \delta_{\text{observed}} \approx \delta_{\text{binary}} \times \frac{\text{light from the binary}}{\text{total light}} $$

This is called a **background binary** or, more generally, a **blend** (a mix). It is treacherous because the light curve can look perfect: U shape, odd equal to even, no visible secondary (it is diluted too).

How to catch it: if the dip comes from another star, the "center of light" of the image shifts slightly during the transit, toward the culprit. This is the **centroid** test. In deep vetting, PlanetHunter also subtracts the out-of-transit image from the in-transit image and sees **where** the light went missing (difference image).

## Telescope glitches

Some dips don't come from any star. They come from the instrument itself. These are the **systematics**.

- **Momentum dumps.** TESS stays pointed using reaction wheels, which build up spin over time. Every so often, small thrusters fire to unload that spin. The pointing shakes for a moment and the measured brightness jumps. If these events repeat at regular intervals, they look like periodic transits.
- **Orbit edges.** At the start and end of each 13.7-day orbit, the telescope changes temperature and the measured brightness slowly rises or falls, in a ramp. When the data cleaning tries to remove this ramp, it can leave behind a depression that looks like a transit.
- **Scattered light.** Near the point of the orbit closest to Earth, light from the Earth and the Moon gets into the cameras and changes the image background.

The trademark of systematics: they happen in **one sector** and don't repeat in the others, or they land exactly on top of momentum dumps and edges.

## The star's own variability

Stars are not perfect light bulbs.

- **Spots and rotation.** Stars spin and have dark spots, like the Sun. When a spot crosses the visible side, the brightness drops; when it leaves, it rises. This creates waves lasting days.
- **Pulsations.** Some stars swell and shrink rhythmically, over minutes or hours.
- **Flares.** Explosions on the surface produce quick brightness spikes **upward**.

PlanetHunter removes the slow variation with a filter (the **detrending**) and clips only the upward spikes. It never clips points downward, or it would erase the transits themselves. When the star varies too fast, the filter leaves leftovers that can look like dips.

## Three real stories from sector 69

These cases happened on PlanetHunter's first day of testing. Each one shows why a stage exists.

### 1. The made-up planet: HD 23472

The star HD 23472 has **5 known planets**. In a single sector, the system saw one transit of planet b and one transit of planet c. With only those two dips, it concluded there was a planet with a **10.29-day** period, which does not exist. The period-based crossmatch didn't catch it, because 10.29 days is not the period of either of the two.

It wasn't an isolated case: the same thing happened with TOI-703 and GJ 143, and all three reached P1, the immediate-alert category. **What fixed it:** **transit-by-transit** matching. Now the crossmatch checks each observed dip: if at least half of them coincide with predicted transits of known objects, and a coincidence that good is unlikely to happen by chance (less than 1 %), the signal is marked as known. The chance check came later: without it, the rule also "explained" random dips, because with loose time windows a coincidence is easy.

### 2. The planet that looked like a binary: WASP-18 b

WASP-18 b is a giant planet, very massive and so hot that it glows. TESS sees its light disappear when it passes **behind** the star: a dip of about **340 ppm** at phase 0.5. This phenomenon is called an **occultation**. The secondary eclipse test saw the dip and vetoed the planet as a binary.

**What fixed it:** the secondary veto now requires the secondary dip to be **at least 10% of the main one**. Planets produce small occultations; companion stars, large ones. On the same day a similar problem showed up: the TESS eclipsing binary catalog contains a few known hot Jupiters (WASP-18 b, WASP-100 b, HATS-16 b). The fix was to give the confirmed planet catalog priority over the binary catalog.

### 3. The best candidate that wasn't: HD 271883

HD 271883 showed a clean signal of **6.61 days** and **4,900 ppm**. It passed every basic test, the centroid was on the target, and there was no known binary. It looked like the perfect candidate.

But the star was observed in **10 sectors**. If the signal were a planet, it should show up strongly in the others: the expected SNR in sectors 67, 68 and 97 was 45 to 64. It did not show up with that strength. It was a glitch in a single sector. **What fixed it:** the **other sectors** test (`other_sectors`), which looks for the signal, including blindly, in the other sectors of the same star.

!!! warning "The general lesson"
    An alert has to survive serious attempts to knock it down. Be suspicious of signals that look too good: all three stories are about signals that looked great.

## How much basic vetting achieves

The project measured basic vetting (no internet) on objects with a known answer in sector 69:

| Group | Signals | Passed | Failed |
|---|---|---|---|
| Confirmed planets (`KNOWN_PLANET`) | 54 | 44 (81%) | 10 (19%) |
| Known false positives (`KNOWN_FP`) | 18 | 8 (44%) | **10 (56%)** |

Read the second row carefully: basic vetting fails **56% of the known false positives**, without any internet lookup, and keeps most of the real planets. But 8 false positives still get through. According to the TFOPWG comments, four of them only show the secondary eclipse when several sectors are added together, one is a binary with an eccentric orbit (secondary away from phase 0.5), two have only a marginal V shape and one is a background binary. That is why deep vetting exists: it looks at the pixels, the neighbor stars and the other sectors.

There is always a trade-off. The limit for the V-shape test was chosen by measuring: with the current value, it flags 8 of the 18 false positives, but it also flags 3 of 50 real planets (grazing planets, such as HIP 65 A b, LTT 9779 b and TOI-2382 b). Even so, since 2026-10-10 a V shape fails the signal on its own (a **hard fail**), without zeroing its score. The project measured the price and accepted it: a few grazing hot Jupiters per sector are lost, and several binaries stop getting through. You will see how failures add up in lesson [M5](../intermediate/m5-vetting-in-practice.md).

!!! tip "In the tool"
    Each impostor in this lesson has a vetting test (`uv run planethunter vet <run_id>`):

    | Impostor | Tests |
    |---|---|
    | Eclipsing binary | `odd_even` (odd/even), `secondary` (phase 0.5), `secondary_scan` (other phases), `shape` (V or U), `kdr25_grazing` (only grazes the star's edge), `radius` (too large) |
    | Background binary, contamination | `centroid`, `duration`; in deep vetting, `tpf_difference_image` and `gaia_neighbors` |
    | Telescope glitches | `edges_dumps`, `consistency`; in deep vetting, `other_sectors` |
    | Stellar variability | the detrending, in the cleaning stage, and the `consistency` test |

    In the dossier, the **Odd, even and secondary** plot shows three panels side by side: odd transits, even transits and phase 0.5. In the light curve, dotted blue lines mark the momentum dumps. The limits for each test are in `config/thresholds.yaml`, with a comment explaining the reason for each value.

!!! example "Exercise 1"
    The target of a pixel is a bright star. Behind it there is a faint eclipsing binary that contributes **1%** of the pixel's total light. The binary has eclipses that block **50%** of its own light. What depth does TESS measure? What size of planet would that imitate around a star like the Sun?

    ??? success "Show answer"
        Observed depth: $0.50 \times 0.01 = 0.005$, that is, **5,000 ppm** (0.5%).

        Equivalent planet: $R_p/R_\star = \sqrt{0.005} \approx 0.071$. For a 1 R☉ star (109 R⊕), $R_p \approx 0.071 \times 109 \approx 7.7$ R⊕, a planet between the size of Neptune and Saturn. Totally plausible. Only tests that look at **where** the light went missing (centroid, difference image) or that know the neighbor stars (Gaia) unmask this case.

!!! example "Exercise 2"
    Suppose a main transit of 10,000 ppm. At phase 0.5, a dip of 340 ppm appears. Under PlanetHunter's rule, does this secondary veto the signal? What if the dip at phase 0.5 were 2,500 ppm?

    ??? success "Show answer"
        The rule: veto only if the secondary is at least 10% of the main one. 10% of 10,000 ppm is 1,000 ppm.

        - 340 ppm is 3.4% of the main one. **No veto.** It is consistent with the occultation of a hot planet, like WASP-18 b.
        - 2,500 ppm is 25% of the main one. **Veto.** A secondary that large points to a companion that gives off a lot of light: a star, not a planet.

        Notice that the rule does not say "any secondary means a binary". It was adjusted after a real planet was failed.

!!! example "Exercise 3"
    For each description, say what the most likely suspect is and which test would catch it.

    1. Transits 1, 3 and 5 are 8,000 ppm; transits 2, 4 and 6 are 3,000 ppm.
    2. Every dip lands within a few minutes of a dotted blue line in the dossier.
    3. A beautiful signal in one sector; the star has 9 more sectors and the signal shows up in none of them.
    4. During the transit, the image's center of light shifts toward a neighbor star.

    ??? success "Show answer"
        1. **Eclipsing binary** with a true period twice the one found. Test `odd_even`.
        2. **Telescope glitch** (momentum dumps). Test `edges_dumps`.
        3. **Single-sector systematic**, like HD 271883. Test `other_sectors`.
        4. **Contamination by a neighbor star** (probably a background binary). Tests `centroid` and `tpf_difference_image`.

## Lesson checklist

- [ ] I know what an eclipsing binary is and its three marks (V, odd/even, secondary).
- [ ] I can explain why the V shape is a clue and not proof (grazing planets).
- [ ] I can calculate the dilution of a background binary.
- [ ] I can name three telescope glitches and their mark (one sector only, on top of dumps or edges).
- [ ] I know how spots, pulsations and flares get in the way, and why detrending never clips downward.
- [ ] I can tell the three stories (HD 23472, WASP-18 b, HD 271883) and the test that fixed each one.
- [ ] I know that basic vetting fails 56% of the known false positives in sector 69 and keeps 81% of the planets.
- [ ] I did the three exercises without looking at the answer.

## Going further

- Prša et al. (2022), "TESS Eclipsing Binary Stars. I. Short-cadence Observations of 4584 Eclipsing Binaries in Sectors 1–26", *The Astrophysical Journal Supplement Series* 258, 16. The binary catalog that PlanetHunter mirrors. Leaf through the light curve figures to see real eclipses.
- Winn (2010), "Transits and Occultations", arXiv:1001.2010. The section on occultations explains why hot planets like WASP-18 b show a dip at phase 0.5.
- Guerrero et al. (2021), *The Astrophysical Journal Supplement Series* 254, 39. Shows how the TESS team separates planets from false positives; compare it with the "In the tool" table in this lesson.
- The file `docs/benchmarks/2026-10-09-s0069-vetting.md` in the repository. The table "What was measured and fixed" tells, with numbers, every adjustment made to the vetting. You will study it in depth in lesson M5.
