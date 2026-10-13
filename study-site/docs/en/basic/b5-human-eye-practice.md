# B5. Practice with human eyes

<p class="meta">Basic level · weeks 5–6 · about 6 hours</p>

!!! abstract "In this lesson you will learn"
    - How to take part in Planet Hunters TESS on Zooniverse and what to look for in each light curve.
    - How to run PlanetHunter on a known planet, Pi Men c, and find its signal.
    - How to read a PlanetHunter dossier section by section.
    - How to review the three real stories from sector 69, identifying the test that solved each one.

## Why train your eye

The previous lessons gave you the ideas. This one is about practice. Algorithms are fast and tireless, but a trained human eye is still very good at noticing when something "doesn't look like" a transit: a strange step, a dip stuck to a gap, alternating eclipses. Every final decision about a PlanetHunter candidate goes through a person looking at the dossier. That person is going to be you.

## Part 1. Planet Hunters TESS

**Planet Hunters TESS** is a citizen science project on the **Zooniverse** platform, created in 2018 by researchers at the University of Oxford. Volunteers look at real TESS light curves and mark the transits they see. Each light curve is seen by several people, and the combined marks point to the signals that deserve scientists' attention.

This is not a game: volunteers in this project have already had candidates that became planets. The first was TOI-813 b, a Saturn-sized planet with a period of about 84 days, published by Eisner and collaborators in 2020. Long periods like that, with few transits, are exactly the ones algorithms have the most trouble finding.

### How to take part

1. Go to the project: [Planet Hunters TESS on Zooniverse](https://www.zooniverse.org/projects/nora-dot-eisner/planet-hunters-tess). Creating an account is optional, but with an account your classifications are recorded and you can comment.
2. Do the **tutorial** that appears the first time. It shows the interface and examples.
3. Open the **Field Guide** on the side. It has examples of transits, binaries, variability and glitches, with the same categories as lesson B4.
4. For each light curve, mark the dips that look like transits and confirm. If there is nothing, confirm without marking anything: "nothing here" is also a useful answer.
5. Use the **Talk** forum to ask about strange light curves. Experienced volunteers and scientists chat there.

!!! note "If the interface changes"
    Zooniverse projects evolve and sometimes pause between batches of data. If Planet Hunters TESS is paused when you get there, explore the Field Guide and the Talk forums, which stay open, and come back when there is new data.

### What to look for in each light curve

| You see | It is probably | Related test |
|---|---|---|
| Identical dips with a flat bottom, repeating at regular intervals | a planet transit | — |
| Deep, pointed dips (V) | an eclipsing binary | `shape` |
| Dips that alternate: one deep, one shallow | an eclipsing binary | `odd_even` |
| A smaller dip exactly between two larger ones | a binary's secondary eclipse | `secondary` |
| Smooth waves lasting several days | spots and the star's rotation | detrending |
| Quick spikes **upward** | flares | spike clipping |
| A dip or ramp stuck to a gap in the data | an orbit edge (glitch) | `edges_dumps` |
| A single dip that never repeats | a single transit, or a glitch | `n_transits` |

**Goal from the plan:** classify at least **200 light curves**. It sounds like a lot, but each one takes less than a minute once you get the hang of it. By around the hundredth, you will notice that your eye already tells transit, binary and glitch apart without thinking.

!!! tip "Study tip"
    Keep a notebook. Write down the numbers of the light curves that left you unsure and what you decided. Later, compare with the discussions on Talk. This notebook is the start of the "review notebook" that the plan recommends for the rest of the course.

## Part 2. Pi Men c in PlanetHunter

Now you are going to run the tool on a planet we already know exists. This has a purpose: learning to read the output when the answer is known, before looking at unknown signals.

**Pi Mensae** (TIC 261136679) is a bright star, similar to the Sun, in the southern hemisphere sky. It has two known planets:

- **Pi Men b**: a giant with an orbit of several years, found by radial velocity in 2001. It does not transit.
- **Pi Men c**: a super-Earth of about 2 R⊕, with a period of **6.27 days** and a depth of **about 300 ppm**. It was the **first** transiting planet announced from TESS data, in 2018, and it is TOI-144.01.

The star lies near the south ecliptic pole, so it has been observed in many sectors.

### Step by step

Before you start, install the project (just once) and update the catalog mirrors. Without up-to-date mirrors, the system cannot tell whether a signal is known.

```bash
uv sync
uv run planethunter mirrors sync
uv run planethunter mirrors status
```

`mirrors status` shows the age of each catalog and its limit. Each one must be within its own limit (48 hours for the TOIs, the CTOIs and the NASA archive; longer for catalogs that change slowly) and every line must say `ok`.

**1. Run the end-to-end analysis for Pi Mensae.**

```bash
uv run planethunter run-target 261136679
```

This command does everything for a single star: it downloads the light curves from MAST, cleans them, searches for signals by combining all sectors, compares them with the catalogs, runs basic vetting and produces a dossier for each strong signal. The first time, the download takes a few minutes. For something faster, limit it to one sector with `--sectors 1`.

At the end, it prints a `run_id=...` line, a table with one row per signal (strongest to weakest) and the path to each dossier. The columns:

| Column | What it is | What to expect for Pi Men c |
|---|---|---|
| `signal_id` | signal number in the database | an integer |
| `period_days` | period in days | close to 6.27 |
| `t0_btjd` | time of one transit, in BTJD | a number with decimals |
| `depth_ppm` | depth | close to 300 |
| `duration_hours` | duration | a few hours |
| `sde`, `snr` | signal strength | above 9 and 7.1 |
| `n_transits` | transits with data | several (many sectors) |
| `match_class` | crossmatch result | `KNOWN_PLANET` |
| `matched_name` | what it matched | the name of Pi Men c |
| `verdict`, `score` | basic vetting result | `PASS_BASIC`, score close to 1 |

If you see ``WARNING: mirrors missing or stale; run `planethunter mirrors sync`.``, run `mirrors sync` again. If other weak signals appear, that's normal: after finding and erasing the strongest signal, the search looks again and sometimes finds noise.

**2. Open the dossier.** The last lines say something like:

```text
dossier for signal 1234: data/dossiers/tic261136679_sig1234.html
```

Open the file for the ~6.27-day signal in your browser. If you want to generate it again later, use `uv run planethunter dossier <signal_id>`.

### Reading the Pi Men c dossier, section by section

Go through the dossier from top to bottom. For each section, the first sentence says what it shows; the second, what to look for.

1. **Header and pills.** Severity, crossmatch class, vetting verdict with the score, and "known host". For Pi Men c: crossmatch `KNOWN_PLANET` and known host "yes" (the star has cataloged planets). The severity shows as "—", because known signals don't become candidates or alerts. The title says "Signal TIC ...": the word "Candidate" only appears for new signals that passed vetting.
2. **Parameters.** A table with the star's Tmag, temperature, radius and mass, sectors, period, fitted depth, duration (T14), planet radius (Rp), SDE/SNR and number of transits. **Check:** the period close to 6.27 days, the depth close to 300 ppm and Rp close to 2 R⊕. Use the rule from lesson B2: $R_p \approx R_\star\sqrt{\delta}$ with the R* from the table. Does it match? Also notice the Tmag: Pi Mensae is very bright (Tmag around 5), which explains why such a shallow transit is detectable.
3. **Light curve.** All the brightness over time, already cleaned. **Red** lines mark the transits; **dotted blue** lines, the momentum dumps. **Look for:** the red transits spread across the sectors, without systematically lining up with the blue lines or with the edges of the gaps. At 300 ppm, you probably **won't** see each individual transit by eye, and that's fine.
4. **Folded transit.** All transits stacked on top of each other, aligned by the period. Gray points are individual measurements; black points are averages; the red curve is the fitted model. **Look for:** a clear "U" in the black points, with the red curve running through them. This is where the transit that was invisible in the full light curve shows up: adding many transits together reduces the noise (lesson B2).
5. **Odd, even and secondary.** Three panels: odd transits, even transits and phase 0.5. **Look for:** the first two with the same depth and the third one flat. That is what a planet does.
6. **Depth per transit.** One point per transit, with the average as a dashed line. **Look for:** points scattered around the line, with none much deeper than the others. In a shallow signal like this one, the scatter between points is large: that is the noise of each individual transit.
7. **TPF difference image.** This section only appears when deep vetting has run, and deep vetting only runs for new candidates. For Pi Men c, it does **not** appear. For a candidate, the red `x` (where the light went missing) should land inside the orange circle (the star's position in the catalog).
8. **Vetting table.** One test per row, with value, threshold, result and note. **Look for:** which ones passed and, if any failed, read the note. Deep vetting tests may show up as "pending".
9. **Crossmatch.** Class, number of known objects on the star and its neighbors, what the signal matched, and the age of each catalog at the time of the comparison. **Look for:** a match with Pi Men c and every catalog within its age limit (48 hours for the TOIs, the CTOIs and the NASA archive).
10. **Next action.** For Pi Men c: "None: known signal or failed vetting." For a new candidate that passed, this is where the suggestion of deep vetting and submission as a CTOI appears.

At the bottom, **Provenance** records the `run_id`, the pipeline version and the detrending window used in each sector. That is what lets you reproduce the analysis later.

!!! tip "In the tool"
    The full usage guide, with more commands, is in the [hands-on PlanetHunter manual](../lab/using-planethunter.md). Dossiers live in `data/dossiers/`. That folder has dossiers for other sector 69 signals; after reading the one for Pi Men c, open two or three of them and compare.

!!! example "Exercise 1"
    After running Pi Men c, answer using the numbers from **your** dossier:

    a) What period and depth were found? How close are they to 6.27 days and 300 ppm?

    b) Use the R* from the dossier and the depth to calculate Rp. Does the result match the Rp the dossier shows?

    c) How many transits with data did the system count? Why is this number much larger than the 4 transits of a single sector?

    ??? success "Show answer"
        a) The period should come out very close to 6.27 days (the difference is usually in the third or fourth decimal place) and the depth in the range of a few hundred ppm, close to 300. Differences of tens of ppm are normal: the depth depends on the fitted model and on how the data was cleaned.

        b) With R* around 1.1 R☉ and a depth of 300 ppm: $\sqrt{0.0003} \times 1.1 \times 109 \approx 2.1$ R⊕. The dossier calculates it exactly this way ($R_p = R_\star\sqrt{\delta} \times 109.076$), so it should match, differing only by rounding.

        c) `run-target` combines **all the sectors** in which the star was observed. Pi Mensae lies near the south ecliptic pole and has many sectors of data, each with about 4 transits. More transits added together give a much higher SNR, and that is why a signal of only 300 ppm comes out so clearly in the folded transit.

## Part 3. Reviewing the three stories

Reread the section "Three real stories from sector 69" in [lesson B4](b4-false-positives.md). For each story, answer in your notebook, in your own words, before opening the answer:

1. What did the system see?
2. Why did it look good?
3. What clue revealed the problem?
4. Which test or change solved it?

!!! example "Exercise 2"
    Fill in the table for the three stories.

    | Case | What it looked like | What it was | Test or change that solved it |
    |---|---|---|---|
    | HD 23472 | ? | ? | ? |
    | WASP-18 b | ? | ? | ? |
    | HD 271883 | ? | ? | ? |

    ??? success "Show answer"
        | Case | What it looked like | What it was | Test or change that solved it |
        |---|---|---|---|
        | HD 23472 | a new 10.29-day planet | one transit of planet b and one of planet c, joined into a false period | **transit-by-transit** crossmatch: if at least half of the dips coincide with predicted transits of known planets, and that is unlikely to be chance, the signal is known |
        | WASP-18 b | an eclipsing binary (dip at phase 0.5) | a planet so hot that its light disappears when it passes behind the star (occultation, about 340 ppm) | the `secondary` test vetoes only when the secondary is at least **10%** of the main one |
        | HD 271883 | the perfect candidate: 6.61 days, 4,900 ppm, passed everything | a glitch in a single sector | `other_sectors` test: the signal did not reappear with the expected strength (SNR 45–64) in sectors 67, 68 and 97 |

        Notice the pattern. In the first case, the error was in the **crossmatch** (it called "new" something that was known). In the second, vetting was **too strict** (it failed a real planet). In the third, basic vetting was **too loose** for this kind of glitch and needed an extra stage. A reliable system has to make few mistakes in all three directions.

!!! example "Exercise 3"
    In the light curve of a dossier, you see three transits marked in red. Two of them land exactly on dotted blue lines, and the third lands at the end of a stretch of data, right before a gap. The folded transit shows a nice "U". What do you conclude?

    ??? success "Show answer"
        Strongly suspect a **telescope glitch**. The dotted blue lines are momentum dumps, and the end of a stretch of data is an orbit edge, where ramps appear. All three dips coincide with problematic moments. The nice "U" in the folded transit doesn't save the signal: it only shows that the dips look like each other, not where they came from. The `edges_dumps` test should have failed; check the vetting table. The next step would be to see whether the star has other sectors and whether the signal shows up in them.

## Lesson checklist

- [ ] I did the Planet Hunters TESS tutorial and read the Field Guide.
- [ ] I classified at least 200 light curves on Zooniverse.
- [ ] I ran `uv run planethunter run-target 261136679` and found the 6.27-day signal with class `KNOWN_PLANET`.
- [ ] I ran the vetting and generated the Pi Men c dossier.
- [ ] I found the period, the depth and the transits marked in red in the dossier.
- [ ] I went through the ten sections of the dossier knowing what to look for in each one.
- [ ] I explained, in my own words, which test solved each of the three stories.
- [ ] I did the three exercises without looking at the answer.

## Going further

- Eisner et al. (2021), "Planet Hunters TESS II: findings from the first two years of TESS", *Monthly Notices of the Royal Astronomical Society* 501, 4669. What the volunteers found in the first two years. Look at the figures with example light curves.
- Eisner et al. (2020), "Planet Hunters TESS I: TOI 813, a subgiant hosting a transiting Saturn-sized planet on an 84 day orbit", *Monthly Notices of the Royal Astronomical Society* 494, 750. The project's first planet, with the story of how volunteers found it.
- Huang et al. (2018), "TESS Discovery of a Transiting Super-Earth in the pi Mensae System", *The Astrophysical Journal Letters* 868, L39. The Pi Men c paper. Compare the numbers in the abstract with those in your dossier.
- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/): search for "pi Men c" and compare period, radius and depth with your dossier, as the project's guide suggests.
