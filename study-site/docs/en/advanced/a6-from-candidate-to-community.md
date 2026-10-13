# A6. From candidate to community

<p class="meta">Advanced level · weeks 13–16 · about 16 hours</p>

!!! abstract "In this lesson you will learn"
    - Who decides each step of the ladder signal → candidate → CTOI → TOI → validated → confirmed.
    - How to use ExoFOP: target pages, community notes, follow-up files.
    - Which fields a CTOI submission needs and how to compute the uncertainties of the ephemeris.
    - What each subgroup of the TESS follow-up program (TFOP) does.
    - How to search the literature on ADS and arXiv before submitting anything.
    - The ethics rules and the checklist for a complete submission package.

Until now, everything happened inside your computer. This lesson is about the moment a candidate leaves it. From then on, other people will spend telescope time on what you sent. That calls for care, honesty and a package of information that lets anyone retrace your reasoning.

## 1. The ladder and who decides each step

| Step | What it means | Who decides |
|---|---|---|
| **Signal** | A periodic dip that passed the detection limits | The pipeline (SDE ≥ 9, SNR ≥ 7.1, ≥ 2 transits) |
| **Candidate** | A new signal that survived vetting and human review | You, with PlanetHunter |
| **CTOI** | A candidate registered on ExoFOP by the community | You submit it |
| **TOI** | Official TESS Object of Interest | The TESS TOI team, which may promote the CTOI |
| **Validated planet** | Very low false positive probability, with follow-up data (usually high-resolution imaging and ground-based photometry) | A peer-reviewed paper |
| **Confirmed planet** | Planetary nature shown by an independent measurement, usually the mass from radial velocity or transit timing variations | A peer-reviewed paper |

PlanetHunter goes, at most, up to the second step. Submitting the CTOI is your act. All the following steps depend on other people and other telescopes. That is why no text of yours, anywhere, should use the word "discovery" for a candidate.

## 2. ExoFOP

**ExoFOP** (exofop.ipac.caltech.edu/tess) is the meeting point for everyone following up TESS targets. It is where the TESS team publishes TOIs, the community submits CTOIs and the observers of the follow-up program record what they did.

### A target's page

Type the TIC number into the ExoFOP search box. The target page usually brings together:

- **Stellar parameters** from the TIC (radius, mass, temperature, Tmag, distance) and alternative names (HD, Gaia, 2MASS).
- **TOIs and CTOIs** associated with the star, with period, epoch, depth, disposition and history.
- **Notes** (observing notes) written by team and community members: "secondary visible in sector X", "visual binary at 3″", "transit confirmed from the ground". **Read them all** before making any decision.
- **Files uploaded** by observers: light curves from ground-based telescopes, high-resolution images with contrast curves, spectra.
- **A summary of the observations** already made: imaging, spectroscopy, time series.
- **Links** to the SPOC Data Validation reports (lesson A2).

To submit CTOIs or write notes, you need to create an ExoFOP account.

!!! info "PlanetHunter already reads ExoFOP"
    The project's `toi` and `ctoi` mirrors are copies of ExoFOP's public tables, synced by `uv run planethunter mirrors sync`. The crossmatch refuses to classify a signal as `NEW` if any mirror is missing or too old for its own limit (48 hours for the TOI, CTOI and NASA Exoplanet Archive tables), and the alert command checks again right before sending. The project also mirrors some published candidate lists (class `KNOWN_PUBLISHED`), but far from all of them. And the **notes** and **files** on the target page are not in the mirrors. Reading them is always your job.

## 3. Before submitting: literature search

Catalogs lag behind. A planet may be in a paper accepted two weeks ago and still not be in the NASA Exoplanet Archive. A candidate may show up in a table of a paper about something else. The literature search is the last line of defense against submitting something already known.

### On ADS

ADS (ui.adsabs.harvard.edu) indexes practically all of the astronomy literature. Strategies:

1. **By object name**: `object:"HD 23472"`. ADS resolves known names through the astronomical object databases and finds papers that mention the star.
2. **By TIC number in the full text**: `full:"TIC 261136679"`. This catches tables and appendices.
3. **By every name**: repeat with the HD name, the Gaia DR3 identifier and the 2MASS name from the ExoFOP page. Older papers do not use TIC.
4. **Sort by date** and read at least the abstracts of the results from the last two years.

### On arXiv

Recent papers appear first on arXiv (arxiv.org), in the **astro-ph.EP** section (planets). The arXiv search looks in the title, authors and abstract, not the full text. So, besides searching by name, browse the listings of the last few weeks of astro-ph.EP looking for work on the same field, the same mission or the same type of object (for example, "TESS single transits").

### What to record

The date of the search, the queries used, the number of results, the relevant papers and the conclusion. In the project, the `research-scout` agent does this sweep before any P0. But the written record is part of the submission package.

## 4. The CTOI submission

The ExoFOP form changes from time to time. Always check the help page before submitting. The usual fields, visible in the columns of the public CTOI table, are:

| Field | Unit | Where it comes from in PlanetHunter |
|---|---|---|
| TIC ID | — | `tic_id` |
| Period and error | days | `period_days` and the fit uncertainty |
| Transit epoch and error | BJD (TDB), full | `t0_btjd` + 2,457,000 |
| Depth and error | ppm | `depth_ppm` from the fit |
| Duration and error | hours | `t14_h` from the fit |
| Planet radius (optional) | R⊕ | `rp_rearth`, with the stellar radius from the TIC |
| User disposition | for example PC | your review decision |
| Notes | free text | summary of the dossier |

### Taking care with the ephemeris

- **BTJD is not BJD.** TESS uses BTJD = BJD − 2,457,000. ExoFOP expects the full BJD. A classic mistake: submitting 3180.45 instead of 2,460,180.45.
- **Choose the epoch in the middle of the data.** Period and epoch come out of a fit correlated with each other. An epoch at the center of the observed span minimizes that correlation and gives the smallest epoch error.
- **Real uncertainties.** The step of the TLS grid is not an uncertainty. Use a transit model fit with an error estimate (for example, MCMC sampling or bootstrap), or at least the width of the periodogram peak, and say which one you used.
- **Propagation.** The uncertainty of a future transit, $n$ orbits later, grows with $n$:

$$
\sigma_{T}(n) = \sqrt{\sigma_{T_0}^2 + n^2\, \sigma_P^2} .
$$

This decides whether ground-based observers can plan an observation, and it is the same reason the project's crossmatch ignores ephemerides with a propagated uncertainty above 1 day.

### The notes

The notes are read by busy people. In a few lines, they should say: how the signal was found (data, sectors, pipeline), what was tested and with what result, what was **not** tested, and which observation would help. Numbers, not adjectives.

## 5. The TESS follow-up program (TFOP)

**TFOP** (TESS Follow-up Observing Program) organizes the observers who follow up TOIs. The working group (TFOPWG) is split into subgroups. Each one tackles different false positive scenarios, and it is worth reading the table with lesson A3 open:

| Subgroup | What it does | Scenarios it eliminates |
|---|---|---|
| **SG1** ground-based photometry | Observes a predicted transit with a ground-based telescope, with pixels much smaller than those of TESS | Neighbors (NEB, NTP): shows which star the transit happens on; checks whether the depth changes with color (binaries tend to change) |
| **SG2** reconnaissance spectroscopy | Moderate-resolution spectra | Spectroscopic binaries, giant or fast-rotating stars; refines the stellar parameters |
| **SG3** high-resolution imaging | Adaptive optics or speckle, produces a contrast curve | Close unresolved companions (PEB, SEB, STP, BEB) |
| **SG4** precise radial velocity | Measures the star's wobble caused by the planet | Measures the mass: this is the path to confirmation |
| **SG5** space-based photometry | Observations with other space telescopes | Refines the ephemeris and the transit shape |

SG1 is the subgroup most open to observers with modest telescopes, including experienced amateurs, for bright targets with deep transits. Taking part requires following the program's rules. The TFOP page at HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html) is the starting point. The AstroImageJ software (Collins et al. 2017) is the standard tool for reducing these observations.

## 6. Ethics

1. **Vocabulary.** Signal, candidate, CTOI, TOI, validated, confirmed. Never "discovery", not on social media, not when talking to a journalist, not "among friends" in a public post.
2. **Cite whoever produced the data.** Every presentation, note or paper cites: the TESS mission (Ricker et al. 2015), the pipeline of the light curve used (SPOC, Jenkins et al. 2016; or QLP, Huang et al. 2020), the TIC (Stassun et al. 2019), Gaia (Gaia Collaboration, Prusti et al. 2016; and Vallenari et al. 2023 for DR3), MAST, and the libraries used (lightkurve, astropy, TLS, wotan, triceratops). The data are public because many people worked to make them so.
3. **Give credit to whoever saw it first.** If an ExoFOP note or a Planet Hunters TESS volunteer already pointed out the signal, cite them. If the signal is already in a paper, it is not yours to submit as new.
4. **Respect the follow-up data.** Files uploaded by observers to ExoFOP have usage rules. Before using them in your work, read the policy and, when in doubt, ask the authors.
5. **Do not waste telescope time.** Every weak CTOI uses up hours of volunteers and professionals. Submit few, good ones. A CTOI that turns into an obvious false positive at the first observation burns credibility.
6. **Report what failed.** A test you could not run, a middling FPP, a neighbor not ruled out: it all goes in the notes. Hiding a problem is worse than having the problem.

!!! tip "In the tool"
    - The dossier (`uv run planethunter dossier <signal_id>`) already includes links to the target's page on ExoFOP, to the Exoplanet Archive and to SIMBAD, as well as the "Next action" section.
    - The `signals` table records the provenance of every row: sector, light curve author, `pipeline_version` and `run_id`. Copy these fields into the package.
    - `uv run planethunter review <signal_id> follow_up --note "..."` flags the candidate while you prepare the submission.

## 7. Submission package checklist

- [ ] The candidate's HTML dossier, reviewed section by section.
- [ ] Class `NEW` with every mirror within its age limit on the date of the package (48 h for TOI, CTOI and the Archive; write down the ages).
- [ ] The target's ExoFOP page read, including all notes and files.
- [ ] Literature search recorded: date, ADS and arXiv queries, result.
- [ ] Ephemeris: period ± error (d), full BJD epoch ± error, with the epoch in the middle of the data and the error method stated.
- [ ] Depth ± error (ppm), duration ± error (h), estimated radius (R⊕) and the stellar radius used.
- [ ] Complete vetting table: each test with value, limit and verdict, including the "no data" ones.
- [ ] Difference image, Gaia neighbors and the result from other sectors.
- [ ] FPP and NFPP with the main scenarios, or the reason it was not run.
- [ ] Provenance: sectors, light curve author (SPOC/QLP), `pipeline_version`, `run_id`.
- [ ] Prediction of the next transits with uncertainty, to make SG1's job easier.
- [ ] Text of the notes, with numbers and limitations.
- [ ] List of citations.
- [ ] Review by a second person before sending.

!!! example "Exercise 1. Ephemeris for ExoFOP"
    Your fit gave an epoch of 3180.4512 ± 0.0011 BTJD and a period of 7.23492 ± 0.00004 d. (a) What is the epoch in BJD? (b) Predict the transit 50 orbits later, with its uncertainty in minutes. (c) And 1,000 orbits later?

    ??? success "Show answer"
        (a) $3180.4512 + 2{,}457{,}000 = 2{,}460{,}180.4512$ BJD.

        (b) $3180.4512 + 50 \times 7.23492 = 3180.4512 + 361.7460 = 3542.1972$ BTJD, or $2{,}460{,}542.1972$ BJD. Uncertainty: $\sqrt{0.0011^2 + (50 \times 0.00004)^2} = \sqrt{1.21 \times 10^{-6} + 4.0 \times 10^{-6}} = 0.00228$ d ≈ **3.3 min**. Great for planning an observation.

        (c) $\sqrt{0.0011^2 + (1000 \times 0.00004)^2} \approx 0.040$ d ≈ **58 min**, about 20 years later. The ephemeris "ages": the period term dominates. That is why new transit observations are valuable even for planets that are already known.

!!! example "Exercise 2. What is wrong with this note?"
    "We discovered a new, potentially habitable rocky planet around TIC 123456789! Period 14.2 days, FPP 0.02, which confirms it is a planet. Epoch 3201.77."

    ??? success "Show answer"
        1. "We discovered": wrong vocabulary. It is a candidate.
        2. "Rocky": without a mass, the composition is unknown. At most "estimated radius of X R⊕".
        3. "Potentially habitable": an unfounded and sensationalist claim; it does not belong in a technical note.
        4. "FPP 0.02 confirms": FPP does not confirm anything. Besides, 0.02 is above 0.015 and there is no mention of NFPP or high-resolution imaging.
        5. "Epoch 3201.77": it is in BTJD, with no error, and no period with an error.
        6. Missing: sectors, light curve author, tests done and limitations.

        An acceptable version: "Transit candidate on TIC 123456789, sectors 68–69 (SPOC 2 min), P = 14.2031 ± 0.0012 d, T0 = 2,460,201.7712 ± 0.0018 BJD, depth 610 ± 70 ppm, duration 3.1 ± 0.2 h, Rp ≈ 2.3 R⊕ for R* = 0.86 R☉ (TIC). Odd/even and secondary consistent with zero; difference image on target (offset 0.2 ± 0.3 px); no Gaia neighbors able to produce the dip outside the 6″ exclusion radius. Triceratops: FPP 0.02, NFPP < 0.001, main scenario PEB. No high-resolution imaging. SG3 and SG1 suggested." (Hypothetical numbers.)

!!! example "Exercise 3. I found it in a preprint"
    Your candidate passed everything and is `NEW`. In the literature search, you find on arXiv a preprint from three weeks ago that lists the same star with a period compatible with yours, in a table of "resolved single-transit candidates". There is no CTOI on ExoFOP. What do you do?

    ??? success "Show answer"
        1. **Do not submit it as new.** The signal has already been reported. Submitting it would mean taking credit for someone else's work, even unintentionally.
        2. Compare carefully: is the period the same, an alias, or another planet around the same star? If it is a different, incompatible period, it may be an additional planet, and the note should cite the preprint.
        3. If it is the same: record it in your notebook, classify it as known in the review (`rejected --reason already_known`, with the reference in the note) and, if you have something to add (new sectors, a better ephemeris), write to the authors or leave a note on ExoFOP citing their work.
        4. For the project: open an issue suggesting that a literature mirror (ADS/arXiv) be checked before the alert, because the catalogs do not yet reflect the preprint.

## Lesson checklist

- [ ] I know who decides each step of the ladder up to a confirmed planet.
- [ ] I opened the ExoFOP page of at least three targets and read the notes.
- [ ] I can search ADS by object and by full text and browse astro-ph.EP.
- [ ] I can convert BTJD to BJD and propagate the uncertainty of an ephemeris.
- [ ] I know what each TFOP subgroup does and which false positive scenario it eliminates.
- [ ] I put together a complete submission package for a P1 candidate (even a hypothetical one), without sending it.

## Going further

- Guerrero et al. (2021), *The Astrophysical Journal Supplement Series* 254, 39. Reread the part about CTOIs and promotion to TOI, this time from the point of view of the person submitting.
- Ricker et al. (2015), *Journal of Astronomical Telescopes, Instruments, and Systems* 1, 014003. The TESS mission paper; the required citation for any work using the data.
- Collins et al. (2017), *The Astronomical Journal* 153, 77. AstroImageJ, the standard SG1 tool; shows what ground-based photometry can check.
- Eisner et al. (2021), *Monthly Notices of the RAS* 501, 4669. Results from Planet Hunters TESS: how a community of volunteers organizes the submission of candidates, with many single transits.
- TFOP page at HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html). The structure of the program and how to take part.
- ExoFOP help page (exofop.ipac.caltech.edu/tess). The current CTOI submission format and the data usage rules.
