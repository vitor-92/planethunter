# Study plan: from curiosity to searching for exoplanets

For anyone with no background in astronomy who wants to truly understand how people search for planets outside the Solar System and how PlanetHunter works. It complements the [Beginner's Guide](BEGINNERS_GUIDE.md): the guide explains the tool; this plan tells you **what to study, in what order, and how to practice**.

Version of 2026-10-09.

---

## The course site: Planet Hunters

This plan is also available as a course website, **Planet Hunters**, in three languages: **English** (the default), **Spanish** and **Portuguese**. The lessons follow the same levels and modules as this plan, and they live in the repository under:

- `study-site/docs/en` (English)
- `study-site/docs/es` (Spanish)
- `study-site/docs/pt` (Portuguese)

Pick whichever language you are most comfortable with; the content is the same in all three. You can switch languages at any time.

---

## How to use this plan

- **Three levels**: basic, intermediate, advanced. Each one has a goal, modules, hands-on practice with the tool and a self-assessment at the end.
- **Suggested pace**: 4 to 6 hours per week. The timeframes below assume that pace; go at your own.
- **Two tracks in parallel**: the **science** track (astronomy, statistics) and the **programming** track (Python). The programming track is optional at the basic level and required from the intermediate level on.
- **Track your progress**: change `[ ]` to `[x]` in this file when you finish each item.
- **Golden rule**: whenever you learn a concept, look for it in a real PlanetHunter dossier (`data/dossiers/`). Seeing the idea applied makes it stick better than any amount of reading.

| Level | Duration | By the end you can |
|---|---|---|
| Basic | ~6 weeks | Explain the transit method, read a dossier and recognize a "beautiful" transit and an obvious binary |
| Intermediate | ~10 weeks | Understand every vetting test, review candidates with sound judgment and run analyses on your own in Python |
| Advanced | ~16 weeks or more | Read papers in the field, change the system's limits with justification and prepare a CTOI submission |

---

## Basic level: understanding what we are looking for

**Goal:** build intuition. By the end, a light curve should no longer look like a scribble.

### Module B1. The sky, stars and planets (week 1)

- [ ] What a star is, why it shines, typical sizes (red dwarf, Sun, giant).
- [ ] Units of distance and size: solar radius (R☉), Earth radius (R⊕), light-year.
- [ ] What an exoplanet is and how many are known (~6,400 in 2026).
- [ ] The detection methods in one sentence each: transit, radial velocity, direct imaging, microlensing.

**Where to study**
- NASA's exoplanet website (science.nasa.gov/exoplanets): the introduction and "how we find" sections.
- A popular-science book, great for getting started: *The Planet Factory*, Elizabeth Tasker (2017).

### Module B2. The transit method (weeks 2–3)

- [ ] Why the light dips when a planet passes in front of its star.
- [ ] The main rule: **depth ≈ (planet radius / star radius)²**.
- [ ] Period, duration and depth: what each one tells you about the system.
- [ ] Why we only see transits for a small fraction of planets (the alignment has to be almost perfect).
- [ ] What a light curve is.

**Pen-and-paper exercise**
- [ ] Calculate the transit depth of Earth, Neptune and Jupiter in front of the Sun. Radii: Sun 696,000 km, Earth 6,371 km, Neptune 24,622 km, Jupiter 69,911 km. Check against the table in section 1 of the guide (84, 1,300 and 10,000 ppm).
- [ ] Repeat for a red dwarf with a radius of 0.2 R☉. Why is it easier to find small planets around small stars?

### Module B3. The TESS telescope (week 4)

- [ ] What TESS observes, for how long, and why it divides the sky into sectors.
- [ ] Why the TESS pixel is large (21″) and what that causes: several stars in the same pixel.
- [ ] What TOIs and CTOIs are, and who decides what becomes a planet.

**Where to study**
- The TESS mission page on NASA's website and the TESS guide at HEASARC.
- Sections 1 and 2 of the [Beginner's Guide](BEGINNERS_GUIDE.md).

### Module B4. Why almost every signal is false (week 5)

- [ ] Eclipsing binary: two stars eclipsing each other. How its curve differs from a planet transit (V shape, alternating eclipses that differ, secondary eclipse).
- [ ] Contamination: the neighboring star in the same pixel.
- [ ] Telescope defects.

### Module B5. Practice with human eyes (weeks 5–6)

- [ ] **Planet Hunters TESS** (zooniverse.org): classify at least 200 light curves. It is the best eye training there is, and volunteers in this project have had candidates that went on to become planets.
- [ ] In PlanetHunter, run the example with a known planet and open the generated dossier:
  ```
  uv run planethunter run-target 261136679
  ```
  Find in the dossier: the period, the depth, and the transits marked in red.
- [ ] Read section 5 of the guide (three true stories). For each one, explain in your own words which test solved the problem.

### Programming track, basic (optional for now)

- [ ] Basic Python: variables, lists, loops, functions. Free course in Portuguese: *Curso em Vídeo — Python* (Gustavo Guanabara), worlds 1 and 2.

### Basic self-assessment

Answer without looking anything up. If you get at least 5 out of 6 right, move on to the intermediate level.

1. A planet with half the radius of Jupiter transits a star identical to the Sun. What is the approximate depth, in ppm?
2. Why are three evenly spaced transits more convincing than a single one?
3. What does Tmag 6 mean compared with Tmag 13?
4. Name two differences between the curve of an eclipsing binary and that of a planet.
5. Why can a signal come from a star that is not the target?
6. What is the difference between a TOI and a confirmed planet?

---

## Intermediate level: understanding how the tool decides

**Goal:** know the reason behind every PlanetHunter stage and be able to review candidates using your own judgment.

### Module M1. Statistics for signals (weeks 1–3)

- [ ] Mean, median, standard deviation, normal distribution.
- [ ] What "3 sigma" means and why 7 sigma is much more reliable.
- [ ] Signal-to-noise ratio (SNR): why it grows with the square root of the number of points.
- [ ] White noise and **red noise**: why averaging neighboring points does not always reduce the noise.
- [ ] Chi-squared test: how to tell whether several measurements "agree".

**Where to study**
- Khan Academy, statistics track (khanacademy.org; Portuguese version at pt.khanacademy.org): descriptive statistics and the normal distribution.
- For red noise, after the statistics basics: Pont, Zucker & Queloz (2006), *Monthly Notices of the RAS* 373, 231. Read the introduction and the figures.

**In the tool**
- [ ] In the dossier, the "Depth per transit" section is a visual chi-squared test. Find a candidate that failed `consistency` and see why.

### Module M2. Transit physics with a bit of math (weeks 3–5)

- [ ] Kepler's third law: period, distance and the star's mass.
- [ ] Why the transit **duration** depends on the star's density. This is the basis of the `duration` test.
- [ ] Impact parameter: central versus grazing transit, and why the grazing one is V-shaped.
- [ ] Limb darkening: why the bottom of the transit is rounded.
- [ ] Secondary eclipse and occultation: why very hot planets, such as WASP-18 b, show a small dip at phase 0.5.

**Where to study**
- Winn (2010), "Transits and Occultations", free on arXiv (arXiv:1001.2010). Sections 1 to 3. It is the classic text; skip the long derivations on your first read.

**Exercise**
- [ ] Use the formula from the guide (step 5, `duration` test) to estimate the duration of a 10-day transit around a Sun-like star. Compare with a real dossier.

### Module M3. How a period is found: periodograms (weeks 5–6)

- [ ] The idea behind BLS (Box Least Squares): testing many periods with a "box" model.
- [ ] What TLS changes: a realistic transit model instead of a box.
- [ ] What SDE is and why 9 is the limit.
- [ ] Aliases: why P/2 and 2P show up as false peaks.

**Where to study**
- The Astropy documentation on Box Least Squares (docs.astropy.org, timeseries section).
- Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39 (TLS): introduction and figures.

### Module M4. Real TESS data in Python (weeks 6–8)

- [ ] Intermediate Python: NumPy (arrays), pandas (tables), Matplotlib (plots).
- [ ] Official tutorials for the Lightkurve library (lightkurve.github.io): LightCurve objects, flattening (flatten), folding (fold), identifying transit signals.
- [ ] Reproduce on your own the detection of Pi Men c with Lightkurve and compare with the PlanetHunter dossier.

**Where to study**
- *Curso em Vídeo — Python* (in Portuguese), world 3.
- The introductory NumPy and pandas documentation ("getting started").

### Module M5. Vetting in practice (weeks 8–10)

- [ ] For each test in the table in step 5 of the guide, find a real signal that failed it and open its dossier.
- [ ] Compare 5 `KNOWN_PLANET` dossiers with 5 `KNOWN_FP` dossiers. Write down what visually sets them apart.
- [ ] Review at least 10 candidates with the review command and write down the reason:
  ```
  uv run planethunter candidates
  uv run planethunter dossier <signal_id>
  uv run planethunter review <signal_id> rejected --reason eb --note "alternating eclipses"
  ```
  Valid rejection reasons: `eb`, `blend`, `systematic`, `noise`, `already_known`, `other`.
- [ ] Read [benchmarks/2026-10-09-s0069-vetting.md](benchmarks/2026-10-09-s0069-vetting.md) and explain each row of the "What was measured and fixed" table.

**Complementary course**
- *Super-Earths and Life* (Harvard, on edX) or *Astrobiology and the Search for Extraterrestrial Life* (University of Edinburgh, Coursera). Both have modules on exoplanet detection, in accessible language.

### Intermediate self-assessment

If you answer at least 5 out of 6 well, move on to the advanced level.

1. Why does the system require SNR ≥ 7.1 and not ≥ 3?
2. A transit lasts 6 hours around a red dwarf with a 3-day period. Why is that suspicious?
3. What changes in the periodogram if the curve has a large gap in the middle?
4. Why does the centroid test use the "implied source distance" and not only the significance of the offset?
5. Explain, with a drawing, why a binary with period 2P shows different depths in odd and even transits.
6. Open an approved dossier and say which test you would run next before submitting.

---

## Advanced level: thinking like someone who builds and publishes

**Goal:** read the literature, understand PlanetHunter's design choices, change limits with measured justification and take a candidate all the way to submission.

### Module A1. Detection algorithms in depth (weeks 1–3)

- [ ] Kovács, Zucker & Mazeh (2002), *A&A* 391, 369: the original BLS paper.
- [ ] Hippke & Heller (2019), TLS: now in full, with the equations.
- [ ] Detrending: compare biweight, spline and Gaussian processes (GP). Why the window matters (section 3, step 2 of the guide, measured numbers).
- [ ] Searching for monotransits and duotransits: the niche with the most planets left to find.

### Module A2. How missions do vetting (weeks 3–6)

- [ ] Twicken et al. (2018), *PASP* 130, 064502: Kepler/TESS Data Validation (difference imaging, centroids).
- [ ] Thompson et al. (2018), *ApJS* 235, 38: the Kepler DR25 "Robovetter". Compare it with PlanetHunter's tests.
- [ ] Guerrero et al. (2021), *ApJS* 254, 39: the TOI catalog and the TESS team's vetting process.
- [ ] Prša et al. (2022), *ApJS* 258, 16: the TESS eclipsing binary catalog. Understand why it contains confirmed planets (a real bug we fixed).

### Module A3. False positive probability (weeks 6–8)

- [ ] Morton (2012), *ApJ* 761, 6: the statistical validation method (vespa).
- [ ] Giacalone et al. (2021), *AJ* 161, 24: triceratops, used by PlanetHunter.
- [ ] Run the FPP on a known planet and on a known false positive. Compare the scenarios (TP, EB, PEB, NEB...).
- [ ] Understand why a low FPP does **not** remove the need for high-resolution imaging.

### Module A4. Machine learning for triage (weeks 8–11)

- [ ] Shallue & Vanderburg (2018), *AJ* 155, 94: a neural network to classify Kepler signals.
- [ ] Valizadegan et al. (2022), *ApJ* 926, 120: ExoMiner.
- [ ] Understand why your reviews (`planethunter review`) are the training data for the project's future classifier.

### Module A5. Measuring the system: completeness and benchmarks (weeks 11–13)

- [ ] Injection-recovery: injecting synthetic transits into real curves and measuring which ones the system recovers. Read the skill at `.claude/skills/injection-recovery/SKILL.md`.
- [ ] Binomial confidence interval (Wilson): why 91 % recall over 135 objects can be anything between 85 % and 95 %.
- [ ] Make a change to a limit in `config/thresholds.yaml`, run the benchmark before and after, and write up the result in `docs/benchmarks/`.

### Module A6. From candidate to community (weeks 13–16)

- [ ] How ExoFOP works: target pages, community notes, CTOI submission.
- [ ] The TESS follow-up program (TFOP): ground-based photometry, spectroscopy, high-resolution imaging.
- [ ] Literature search on ADS (ui.adsabs.harvard.edu) and arXiv (astro-ph.EP) for a target before any submission.
- [ ] As an exercise, prepare a complete submission package for a P1 candidate, even if you do not send it.

**Reference book to consult:** *Exoplanets*, edited by Sara Seager (University of Arizona Press, 2010).

### Advanced self-assessment

1. Propose a change to the vetting, explain the hypothesis, how you would measure the effect and what result would make you give it up.
2. Explain why a new, deep signal on a star in the TESS continuous viewing zone is almost always a systematic.
3. Read a recent TESS planet paper and identify every vetting test it used and which ones PlanetHunter does not have.
4. Write the text of a CTOI submission for a hypothetical candidate, using the numbers from the dossier.

---

## Map: concept, where it appears in the tool, where to study it

| Concept | In the tool | Level | Where to study |
|---|---|---|---|
| Depth ≈ (Rp/R*)² | `depth_ppm`, `rp_rearth`, `radius` test | Basic | B2, Winn 2010 |
| Light curve and detrending | Step 2, the dossier's "Light curve" plot | Basic/Intermediate | B2, M4, Lightkurve |
| Periodogram, SDE, alias | Step 3, `sde`, `refine_alias` | Intermediate | M3, Hippke & Heller 2019 |
| SNR and red noise | `snr`, `BlockNoise`, `consistency` | Intermediate | M1, Pont+2006 |
| Duration and stellar density | `duration` test | Intermediate | M2, Winn 2010 |
| Eclipsing binary | `odd_even`, `secondary`, `shape`, `gaia_eb` | Basic/Intermediate | B4, M5, Prša+2022 |
| Contamination by a neighbor | `centroid`, `tpf_difference_image`, `gaia_neighbors` | Intermediate/Advanced | A2, Twicken+2018 |
| Single-sector systematic | `other_sectors`, `edges_dumps` | Intermediate | M5, guide section 5 |
| "Does it already exist?" | Step 4, `KNOWN_*` classes | Basic | Guide section 3 |
| False positive probability | `fpp_triceratops`, P0 severity | Advanced | A3, Giacalone+2021 |
| Recall and completeness | `benchmark`, injection-recovery | Advanced | A5 |

---

## Final tips

- **Do not try to read papers cover to cover at first.** Read the abstract, introduction, figures and conclusion. Come back to the equations when you need them.
- **Be suspicious of signals that look too good.** The whole story of the project's first day (guide, section 5) is about perfect signals that turned out to be false.
- **Keep a review notebook.** For every candidate you review, write down what you saw and what you decided. In a few months that notebook will be worth more than any course.
- **Community:** the Planet Hunters TESS forums on Zooniverse and the target notes on ExoFOP are where amateurs and professionals talk about candidates.
