# PlanetHunter explained for beginners

This guide explains, without assuming any background in astronomy, what PlanetHunter does, how each analysis works, how to read the results, and what to study to understand the tool in depth. Technical terms appear in **bold** the first time and are in the glossary (section 2).

Version of 2026-10-13 (updated after the 2026-10-10 code audit). Full technical details: [PLAN.md](PLAN.md). Measured numbers: [benchmarks/](benchmarks/).

---

## 1. The idea on one page

### What an exoplanet is

An **exoplanet** is a planet that orbits a star other than the Sun. As of 2026, about 6,400 confirmed ones are known. Almost none of them can be photographed: they are too far away and the star outshines the planet.

### How to find an exoplanet without seeing it: the transit method

Picture a flashlight switched on at the end of a hallway and a fly passing in front of it. You can't see the fly, but a very sensitive light meter notices that the flashlight got a tiny bit dimmer for a few moments.

Stars work the same way. When a planet passes in front of its star, from our point of view, the brightness drops a little. This is called a **transit**. If the drop repeats at regular intervals, we have the orbit's **period**.

```
brightness
  1.000 ─────────╮      ╭──────────────────╮      ╭─────────
                 │      │                  │      │
  0.999          ╰──────╯                  ╰──────╯
                 ↑ transit                 ↑ transit
                 |←──────── period ───────→|
                                                       time →
```

How much the light drops depends on the size of the planet compared to the size of the star:

| Planet passing in front of a Sun-like star | Brightness drop |
|---|---|
| Earth | 0.0084 % (84 **ppm**) |
| Neptune | 0.13 % (1,300 ppm) |
| Jupiter | ~1 % (10,000 ppm) |

ppm = parts per million. 1,000 ppm = 0.1 %. It is the unit the system uses for transit depth.

### The telescope: TESS

**TESS** is a NASA space telescope launched in 2018. It measures the brightness of hundreds of thousands of stars every 2 minutes (or 20 seconds, or 200 seconds), watching one strip of the sky for about 27 days, called a **sector**. Then it moves on to another strip. By 2026 it has gone through more than 100 sectors and covered almost the entire sky, several times over.

The data are public. Anyone can download and analyze them. That is what PlanetHunter does.

### The hard problem: almost every signal is false

A periodic drop in brightness does **not** prove there is a planet. Many other things produce similar drops:

- **Two stars eclipsing each other** (an eclipsing binary). This is the most common false positive.
- **A neighboring star** that landed on the same telescope pixel and is varying.
- **Telescope glitches**: pointing adjustments, scattered light, the edges of observation stretches.
- **Spots and pulsations** on the star itself.

That is why the real work is not finding brightness drops. It is **ruling out** everything that isn't a planet and **checking** whether what's left hasn't already been found by someone else.

### What PlanetHunter does, in 8 steps

```
 0. MIRRORS         Downloads the lists of already-known planets, candidates and binaries
        │
 1. INGESTION       Downloads TESS brightness measurements (light curves)
        │
 2. CLEANING        Removes glitches and the star's natural variation
        │
 3. SEARCH          Looks for periodic brightness drops
        │
 4. "ALREADY KNOWN?" Compares each signal with the lists from step 0
        │
 5. BASIC VETTING   15 tests that catch common false positives
        │
 6. DEEP VETTING    Looks at the pixels, neighboring stars and other sectors
        │
 7. ALERT           Dossier + message only for what survived and is new
```

---

## 2. Essential glossary

| Term | What it means |
|---|---|
| Light curve | A plot of a star's brightness over time. It is the raw data behind everything. |
| Transit | The brightness drop when something passes in front of the star. |
| Period (P) | Time between two consecutive transits, in days. |
| Depth | How much the brightness drops during the transit, in ppm. |
| Duration (T14) | How long each transit lasts, in hours. |
| ppm | Parts per million. 10,000 ppm = 1 %. |
| Sector | A ~27-day block of TESS observation of one strip of the sky. |
| TIC | TESS Input Catalog. A catalog of stars; each one has a number, e.g. TIC 261136679. |
| Tmag | A star's brightness on the TESS "ruler". A **smaller** number = a **brighter** star. 6 is very bright; 13 is faint. |
| R☉, M☉ | The Sun's radius and mass, used as units for stars. |
| R⊕ | Earth's radius, used as the unit for planets. Jupiter is ~11 R⊕. |
| TOI | TESS Object of Interest. An official candidate announced by the TESS team. |
| CTOI | Community TOI. A candidate submitted by someone outside the team (what you would do). |
| TFOPWG | The group that follows up on TOIs and decides: CP/KP (confirmed planet), PC (planet candidate), FP/FA (false positive/false alarm). |
| Eclipsing binary (EB) | Two stars that eclipse each other. The main planet impostor. |
| Blend / contamination | Light from another star mixed into the same pixel. The signal may come from that star. |
| TESS pixel | Each pixel covers 21 arcseconds of sky. That's large: several stars fit inside one. |
| SDE | Strength of the peak in the periodogram: how much the signal stands out from the noise. Above 9 counts as a detection. |
| SNR | The transit's signal-to-noise ratio. Above 7.1 counts as a clear signal. |
| Red noise | Noise that comes in slow waves lasting hours (the star, the telescope), so it does not average away the way random noise does. |
| S/N_pink | A stricter SNR that also counts red noise. The TESS team's quick-look pipeline asks for at least 9. |
| Periodogram | A plot that tests thousands of periods and shows which ones "fit" the data. |
| Alias | A wrong period that is a multiple or fraction of the true one (P/2, 2P, P/3...). |
| Ephemeris | A prediction of when the next transits will happen (period + one transit time). |
| BTJD | The time unit TESS uses: days since a reference date. |
| Detrending | Removing the slow variation in the star's brightness so the transits become visible. |
| Vetting | A battery of tests to rule out false positives. |
| Veto, hard fail, soft fail | Three strengths of failure in vetting. A veto eliminates the signal on the spot. A hard fail is one serious failure that alone is enough to fail the signal. A soft fail is a warning: one is tolerated, two fail the signal. |
| False positive | A signal that looks like a planet but isn't. |
| Single transit (monotransit) | Only one transit seen; the period remains unknown. |

---

## 3. Each step in detail

For each step: what it does, why it exists, what can go wrong, and where it lives in the code.

### Step 0. Catalog mirrors

**What it does.** Downloads a local copy of 12 lists of known objects:

| Source | What it contains | Must be younger than |
|---|---|---|
| NASA Exoplanet Archive | Confirmed planets (~6,400) | 48 hours |
| ExoFOP TOI | All official TESS candidates (~8,100), with the TFOPWG decision | 48 hours |
| ExoFOP CTOI | Community candidates (~5,100) | 48 hours |
| exoplanet.eu | European planet catalog (~8,300) | 7 days |
| K2 planets and candidates | From the Kepler telescope's second mission (~1,800) | 7 days |
| Kepler KOI table | Kepler's candidates and false positives (~9,600) | 30 days |
| Two TESS eclipsing binary catalogs | Prša et al. 2022 (~4,600) and "TESS Ten Thousand" (Kostov et al. 2025, ~10,000) | never expire (fixed published tables) |
| Four published candidate lists | DIAmante, DTARPS, LEO-Vetter and ExoMiner++ (a few hundred to ~2,500 each) | never expire (fixed published tables) |

**Why.** The system should only alert on what is **new**. To do that it needs to know everything that already exists. The local copies avoid depending on the internet in the middle of the analysis.

**Safety rule.** Each source has its own freshness limit (last column). Lists that change every day, such as the TOIs, must be less than 48 hours old; fixed published tables only need to be present, in the version the code expects. If any copy is missing or too old, no signal can be classified as new. It becomes `UNVERIFIED` and does not trigger an alert. Every download also records the number of rows and a checksum, so you can tell later exactly which copy was used.

**Command.** `uv run planethunter mirrors sync` and `uv run planethunter mirrors status`.

**Code.** [src/planethunter/catalogs/mirrors.py](../src/planethunter/catalogs/mirrors.py).

### Step 1. Ingestion

**What it does.** Downloads the light curve files from the public MAST archive and converts them to a compact format (Parquet). A whole sector has ~20,000 stars.

**For each star it stores:** time, corrected brightness, the error of each measurement, quality flags, the star's position on the detector, and the star's parameters (radius, temperature, brightness, position in the sky).

**Command.** `uv run planethunter ingest sector 69 --limit 2000`.

**Code.** [src/planethunter/ingest/](../src/planethunter/ingest/).

### Step 2. Cleaning and detrending

**What it does.** Three things, in this order:

1. **Removes bad measurements.** TESS flags moments with problems, such as adjustments of the pointing motors ("momentum dumps").
2. **Removes upward spikes** (stellar flares, cosmic rays). It never removes downward points, or it would erase the transits.
3. **Removes the star's slow variation.** Stars rotate and have spots, so their brightness goes up and down over days. A filter (biweight, from the wotan library) estimates this trend over a 1-day window and divides it out.

```
before:  ~~~~\_/~~~~~~~~~\_/~~~~~      (slow wave + transits)
after:   ────\_/─────────\_/─────      (just the transits)
```

**The main caveat.** If the filter window is too short, it "eats" the transit. We measured it: with a 0.5-day window, a 5-hour transit lost 40 % of its depth. With 1 day, it loses 6 %. But on stars that vary quickly, 1 day leaves residual variation behind. That's why the system makes **two versions** when it detects leftover variation, and searches both. To decide whether there is leftover variation it uses a robust measure (based on the median), so that a deep transit is not mistaken for variability.

**A second cleaning, just for vetting.** Once a signal is found, the system cleans each sector again before testing it: with that sector's own window (never shorter than 3 times the transit duration) and with the transits **hidden** from the filter, so the filter cannot eat them. With this, a 12-hour transit keeps 99 % of its depth instead of 50 %.

**Code.** [src/planethunter/preprocess/clean.py](../src/planethunter/preprocess/clean.py) and [src/planethunter/search/target.py](../src/planethunter/search/target.py).

### Step 3. Searching for periodic signals

**What it does.** For each star, it tests thousands of possible periods and, for each one, thousands of transit positions and durations. It measures how much better a transit model explains the data than a flat line does. The algorithm is **TLS** (Transit Least Squares). Its transit model has the darker edges of a star ("limb darkening") as seen through the TESS filter.

**Which periods.** From about 0.2–0.3 days (the shortest orbit that stays at least 2 star radii from the star's center; it depends on the star's size) up to 40 days, and never more than 90 % of the time span of the data. In a single sector of ~27 days, that means up to ~24 days.

The result is a **periodogram**: a plot with a peak where the period "fits".

```
strength
  │            ▲ peak at 3.7 days → high SDE
  │            │
  │  .  . .  . █ .   .  .   ▲ (alias at 7.4 d)
  │ ...........█.....:.....:█......
  └──────────────────────────────── period (days)
```

**Two measures decide whether it is a signal:**

| Measure | Question it answers | Threshold |
|---|---|---|
| SDE | Does the peak stand out from the rest of the periodogram? | ≥ 9 |
| SNR | Is the drop large compared to the star's noise? | ≥ 7.1 |

**What the system measures by itself.** TLS gives the period, the transit time, the depth and the SDE. The rest is measured again by the project, because it has to be right for every later step:

- **Duration.** TLS reports a duration shrunk by the fraction of time that has data (with two sectors years apart, a 3-hour transit came out as 0.23 hours). The system undoes this and stores the real duration.
- **SNR.** Measured on the data with that real duration and a robust noise estimate.
- **S/N_pink.** A second SNR that also counts red noise, the slow wiggles that last hours (section 2). It is stored for vetting.
- **Number of transits.** A transit only counts if at least half of its expected time has data. A transit that falls mostly in a gap does not count.

**Iterative search.** After finding the strongest signal, the system erases those transits and searches again. That way it finds a second or third planet around the same star.

**Alias correction.** With few transits and gaps in the data, TLS sometimes returns a third of the true period. The system tests 2P and 3P: if the "extra" transits predicted by P fall on data and show no drop, the true period is the longer one. The SNR is then measured again with the transits of the true period only.

**How we know it works.** Recall benchmark: we take 135 known official candidates from sector 69 that are detectable within one sector and ask whether the system finds them. Result before the 2026-10-10 changes: **91.1 %** (a rerun is pending). Details in [benchmarks/2026-10-09-s0069-history.md](benchmarks/2026-10-09-s0069-history.md).

**How often noise fools it.** The search can also run on "null" versions of the light curves: flipped upside down (dips become bumps) or with each orbit shifted in time. Any "transit" found there is false by construction. Counting them measures the false-alarm rate, the method the Kepler team used (Thompson et al. 2018).

**Command.** `uv run planethunter search --sector 69`. Null runs: `--null inverted` or `--null scrambled`.

**How many CPU cores it uses.** By default, all but one. To use fewer (for example, to keep working on the computer), set `PLANETHUNTER_MAX_WORKERS=4` in your `.env` file (section 6). It caps the search, the vetting and the deep vetting, whatever the command line or the configuration asks for; each process uses one core. Downloads are not affected.

**Code.** [src/planethunter/search/tls.py](../src/planethunter/search/tls.py).

### Step 4. "Already known?" (crossmatch)

**What it does.** For each signal, it answers two separate questions.

1. **Which star?** By TIC number or by position in the sky (within 21″, one pixel). Stars move slowly across the sky, so the star's position is moved forward from the catalog date to the date of the observation (its "proper motion").
2. **Which signal?** Four ways to match:
   - **Same period** (or an alias: 2×, ½, 3×...), with the transit times lining up. The tolerance grows with the uncertainty of our period, up to 3 %.
   - **Individual transits**: does each observed drop coincide with the predicted transit of some known object? This catches the case where the system combined transits from **two different planets** and invented a fake period. It really happened with HD 23472, a star with 5 planets. Two conditions: at least half of the transits must coincide, **and** the coincidence must be unlikely to happen by chance (less than 1 %). The first version of this rule matched random signals about a third of the time; this one does so well under 1 % of the time. Near misses stay `NEW`, with a warning.
   - **Whole-number multiples** of a known period on the same star (up to 50× or 1/50), only when the transit times also line up.
   - **Known neighbor** within 2′ with the same period: the signal probably comes from it.

**Output classes:**

| Class | Meaning | What the system does |
|---|---|---|
| `KNOWN_PLANET` | Already-confirmed planet | Nothing; it serves as a test |
| `KNOWN_TOI` / `KNOWN_CTOI` | Already a TESS candidate | Nothing |
| `KNOWN_PUBLISHED` | Already in a published candidate list (Kepler, K2, DIAmante, DTARPS, LEO-Vetter, ExoMiner++) | Nothing |
| `KNOWN_FP` | Already flagged as a false positive or binary. A cataloged binary matches at **any** alias (2×, ½...), because a binary's two eclipses easily fool the period. | Discards it |
| `NEARBY_KNOWN` | Known neighboring object with the same period | Discards it (contamination) |
| `NEW` | Nothing matched | Moves on to vetting |
| `UNVERIFIED` | Would be new, but some catalog is missing or stale | No alert |

**Heads-up.** A known star with a **new** period is `NEW` (with a "known host" warning). That's how additional planets are found in systems that have already been studied.

**Checks across the whole run.** Some problems only show up when you look at all the stars of a run together:

- **Epoch spikes.** If many unrelated stars have a "transit" at the same moment, the cause is the telescope, not the stars. The system counts transits in 6-hour bins and flags the bins with far more stars than chance allows. A signal with half or more of its transits in those bins never generates an alert.
- **Shared signals.** The same period and transit time on two stars within 2′ means that one star's light is leaking into the other's pixels. The star that can really produce the drop is the `source`; the other is the `victim` and gets no alert. Two entries less than 2″ apart are a `duplicate` of the same star in the TIC catalog, and also get no alert.

**Code.** [src/planethunter/crossmatch/core.py](../src/planethunter/crossmatch/core.py) (one signal at a time) and [src/planethunter/crossmatch/runlevel.py](../src/planethunter/crossmatch/runlevel.py) (checks across the run).

### Step 5. Basic vetting (no internet)

Each test answers one question. A failure comes in three strengths:

- **Veto**: the signal is eliminated on the spot.
- **Hard fail**: one serious failure. On its own, it fails the signal.
- **Soft fail**: a warning. One soft fail is tolerated; two or more fail the signal.

A test can also end with **no data** (for example, a star with no known radius). That is not a failure.

| Test | Question in plain language | Catches what | Strength of the failure |
|---|---|---|---|
| sde, snr | Is the signal strong enough? | Noise | Veto |
| snr_pink | Is the signal still strong once slow, correlated wiggles of the star (red noise) are counted? (S/N_pink ≥ 9) | Noise that mimics a transit over hours | Soft (a veto can be switched on in the configuration) |
| n_transits | Did we see at least 2 transits (each with at least half of it covered by data)? | A single event with no period | Veto |
| independence | Does this signal survive if we erase the stronger signals from the same star? | An echo of another signal | Veto |
| odd_even | Do the odd and even transits have the same depth? | A binary whose real period is 2× longer (alternating eclipses that differ) | Soft; veto if very different (5σ) |
| secondary | Is there a smaller drop halfway between transits? | A binary's secondary eclipse | Soft; veto if large (5σ **and** at least 10 % of the main drop) |
| period halving | Is the "secondary" just as deep and as long as the main drop? Then it is another transit: the signal was found at twice the true period. | Detection at 2P | Not a failure: the signal is tested again at half the period |
| secondary_scan | Is there a drop at some other phase? | A binary with an eccentric orbit | Hard |
| shape | Does the transit have a flat bottom (U) or a pointy one (V)? | A grazing binary (V shape) | Hard |
| kdr25_grazing | A physical transit model (with the star's darker edges, "limb darkening") gives the planet size k and how off-center it crosses (b). Does it only graze the star's edge (k + b > 1.04)? | A grazing binary | Soft |
| radius | Is the resulting "planet" planet-sized? (size from that model when the transit is not grazing) | An object that is too big (a star) | Soft above 2× Jupiter. Veto above 3× Jupiter only if the star's size is reliable **and** there is another sign of a binary (V shape, odd/even or secondary) |
| duration | Does the duration match the star's size and mass? (between 0.15 and 1.67 times the prediction) | A signal coming from another star; an extreme grazing transit | Soft |
| centroid | Does the position of the light shift during the transit? | A signal coming from a neighboring star | Soft. No data for very bright stars (Tmag < 7, saturated) or with fewer than 3 transits |
| edges_dumps | Do the transits fall on the edges of observations or on telescope adjustments? | Instrumental glitch | Soft |
| consistency | Do all the transits have similar depths? | One odd event dominating | Soft |

**Verdict.** The signal fails if it has any veto, any hard fail (`shape`, `secondary_scan`, and in deep vetting `tpf_difference_image` and `fpp_triceratops`) or more than one soft fail. Otherwise it passes (`PASS_BASIC`).

**Score.** It starts at 1.0. Each failure multiplies it by a weight (0.3 to 0.6), each test with no data by 0.95, and a veto sets it to zero. The score no longer decides pass or fail: it only **ranks** the signals, and severity (step 7) uses it.

**How we know it works.** We run the vetting on objects with a known answer in sector 69. Details in [benchmarks/2026-10-09-s0069-vetting.md](benchmarks/2026-10-09-s0069-vetting.md). These are the results measured before the 2026-10-10 changes; a new measurement is pending.

| Group | Passed |
|---|---|
| Confirmed planets | 77–84 % |
| Confirmed false positives | 11–44 % |

In other words: basic vetting keeps most real planets and knocks out most false ones, but not all of them. That's why step 6 exists.

**Command.** `uv run planethunter vet <run_id>`. It prints this validation table for every run.

**Code.** [src/planethunter/vetting/basic.py](../src/planethunter/vetting/basic.py).

### Step 6. Deep vetting (with internet, candidates only)

It only runs for whatever passed the basic vetting, because it is slower.

| Test | What it does | Catches what |
|---|---|---|
| tpf_difference_image | Downloads the pixel images. Subtracts the in-transit image from the out-of-transit image. Whatever "dimmed" shows up in the difference. Compares where it is with the star's catalog position (moved forward with its proper motion). It fails if the difference is more than 1 pixel away and the offset is significant; with fewer than 3 transits there is no way to tell. A hard fail. | A neighboring star being the source |
| gaia_neighbors | Lists neighboring stars (Gaia catalog). For each one: if it were the source, how much would it have to dim? It models how much of each star's light falls inside the pixels used. More than 100 % is impossible. It fails if a neighbor that could do it sits where the difference image points. | Neighbors that could produce the signal |
| gaia_eb | Is the star in Gaia's eclipsing binary catalog? | A known binary |
| simbad_type | What does the SIMBAD database say this star is? It only fails for binary types (eclipsing, spectroscopic or ellipsoidal binary); other types, such as variable or young stars, are shown as information. | Known binaries |
| other_sectors | Does the signal show up again in **other** sectors in which the star was observed? Also runs a blind search, without hinting at the period. | A glitch confined to a single sector |
| fpp_triceratops | Uses a statistical model (triceratops) to compute the probability that the signal is a false positive (FPP), taking into account the star, its neighbors and the shape of the transit. It runs 3 times and takes the average, using the noise actually measured in the light curve. It fails if FPP ≥ 0.5 or if NFPP (the part that blames a known neighbor) is above 0.1. A hard fail; NFPP above 0.5 is a veto. | Binary scenarios that mimic a planet |

**The other-sectors test is the most powerful.** A real planet always transits. A telescope glitch happens once. In the first real test, with 2164 stars, the two "best candidates" vanished exactly here: the signal was not in the other sectors at the expected strength.

**A subtlety we measured.** Searching for a signal within a narrow range of periods always finds *something* in the noise. On stars with no signal, this gives an SNR above 19 in 10 % of attempts. That's why the system measures each star's "noise floor" (the same search at 40 random periods, with the candidate's own transits hidden so they do not raise the floor) and only counts a detection above it.

**FPP** (false positive probability) ranges from 0 to 1. Below 0.5: a plausible candidate. Below 0.015, with NFPP below 0.001: the level the literature uses to "validate" a planet, but only after high-resolution imaging taken by another telescope. Example: the known planet WASP-100 b got an FPP of 0.35. These levels only hold for planets smaller than 8 R⊕, SNR of at least 15 and 2-minute data (Giacalone et al. 2021); outside that region the dossier says so. Each run takes ~6 minutes, so ~18 minutes per candidate for the 3 runs, and it only runs for whatever passed everything else.

**Command.** `uv run planethunter vet-deep <run_id>`.

**Code.** [src/planethunter/vetting/deep.py](../src/planethunter/vetting/deep.py).

### Step 7. Severity, dossier and alert

Severity only applies to `NEW` signals. Two numbers feed it: the vetting **score** (step 5) and, when the model exists, **p_rank**, a probability learned from known planets and known false positives (`uv run planethunter calibrate`). The model's two thresholds, `p1_cut` and `p2_cut`, are chosen by measuring how many known planets each one keeps.

| Level | When | What happens |
|---|---|---|
| none | Not `NEW`; any veto; half or more of the transits on epoch spikes; a shared-signal `victim` or `duplicate`; failed vetting with p_rank below `p2_cut` | Nothing |
| P0 | Passed vetting, score ≥ 0.8 **and** p_rank ≥ `p1_cut`, **plus** complete deep vetting (difference image and Gaia neighbors passed, FPP computed) with FPP < 0.1, NFPP < 0.001, planet smaller than 8 R⊕, SNR ≥ 15 and 2-minute data | Immediate alert |
| P1 | Same as P0, but deep vetting is incomplete or the signal is outside that region | Immediate alert |
| P2 | Passed vetting but below the P1 thresholds; or failed vetting (no veto) but rescued by p_rank ≥ `p2_cut`; or a warning that caps it: the star is a cataloged binary, the star has no known radius, NFPP > 0.1, the signal is the `source` of a shared signal, the star has a known object with no period, or the transits partly coincide with a known object | Review queue (no immediate alert) |

**The model only lowers priority.** A high p_rank never raises a signal above what the score allows, and a failed signal can be rescued at most to P2. The candidate list also shows **p_abs**, the same probability corrected for how rare planets are among new signals. That correction rests on an assumption (5 % of new signals being planets), so p_abs is for reading only and severity never uses it.

**Right before sending**, the system checks the crossmatch again against freshly loaded catalog copies. If any copy is stale or the signal is no longer `NEW`, the alert is not sent. The same target with the same period is not alerted twice within 30 days.

For each candidate the system generates an HTML **dossier** in `data/dossiers/`, explained in section 4.

Alerts go to Telegram or Discord if configured (section 6). Without configuration, they stay in `data/outbox/` for you to read.

**Code.** [src/planethunter/alerts/](../src/planethunter/alerts/).

---

## 4. How to read the results

### The candidate list

`uv run planethunter candidates <run_id>` shows a table. Columns, from left to right:

| Column | How to read it |
|---|---|
| severity | P0 or P1 = look now. P2 = look when you can. |
| signal_id | Signal number. Use it in `planethunter dossier <signal_id>`. |
| tic_id | Star number. Paste it into exofop.ipac.caltech.edu to see everything about the star. |
| tmag | Brightness. Below 10 is bright: easier to confirm with other telescopes. |
| sectors | TESS sectors used in the search. |
| period_d | Period found by the search, in days. If vetting halved it (`period_halved`), the dossier shows the period actually tested. |
| depth_ppm | Depth. Above ~20,000 ppm (2 %), suspect a binary. |
| t14_h | Duration in hours. |
| rp_rearth | Estimated planet size in Earth radii. 1–4 = rocky to mini-Neptune; 4–8 = Neptune; 8–20 = giant; above 22 = probably not a planet. |
| sde, snr | Signal strength. The higher, the better. |
| n_transits | How many transits were seen. 2 is the minimum; more is better. |
| score | Vetting score (0 to 1). A ranking, not a probability. |
| p_rank | The model's probability (0 to 1) used to rank and to lower priority. Empty if no model has been trained. |
| p_abs | The same probability corrected for how rare planets are among new signals. For reading only; it rests on an assumption. |
| failed | Tests that failed without vetoing. Read the dossier to understand them. |
| epoch_spike_frac | Fraction of the transits that fall on epoch spikes (many stars "transiting" at the same time). 0.5 or more: a telescope effect, no alert. |
| shared_signal_role, shared_signal_tic | If another star within 2′ has the same signal: `source`, `victim` or `duplicate`, and which star it is. |
| periodless_known_on_host | `True` if the star has a known object with no period; the signal could be it. |
| host_known | `True` if the star already has other cataloged objects. |
| review_status | Your decision with `planethunter review`. |

### The dossier, section by section

Open the HTML file in your browser.

1. **Header and "pills".** Severity, crossmatch class, verdict and score. If you see `known host: yes`, the star already has planets or candidates. It could be an additional planet, or the system may have mixed up transits.
2. **Parameters.** Check whether the planet's radius makes sense and whether the star has a radius (R*). With no R*, be suspicious. "Vetted period" is half the found period when vetting decided the signal had been found at twice its true period.
3. **Light curve.** Red lines mark the transits; dotted blue lines, the telescope adjustments. **Bad sign:** transits stuck to blue lines or at the edge of a stretch of data.
4. **Folded transit.** All transits stacked on top of each other. **Good sign:** the black dots form a clear "U", and the red curve runs through them. **Bad sign:** a pointy "V", or scattered dots with no shape.
5. **Odd, even and phase 0.5.** **Good sign:** the first two panels have the same depth, and the third is flat. **Bad sign:** different depths (binary) or a drop in the third (secondary eclipse).
6. **Depth per transit.** **Good sign:** dots lined up on the dashed line. **Bad sign:** one dot much deeper than the others.
7. **Difference image.** Left: the normal star. Right: what dimmed. **Good sign:** the red `x` (where the light went missing) lands inside the orange circle (the star's catalog position). The white `+` marks the center of light outside the transit. **Bad sign:** the `x` is more than a pixel away from the circle (a neighbor).
8. **Vetting table.** One test per row. "VETO" or "fail" in red; "no data" or "pending" highlighted as a warning. Read the note next to it.
9. **Crossmatch.** What the signal was compared against, any warning notes, and the age of each catalog.
10. **Next action.** What to do with this candidate.
11. **Provenance.** The run, the pipeline version and the detrending window used in each sector, so the analysis can be repeated.

### The validation table (shown when you run `vet`)

| Column | How to read it |
|---|---|
| class | Crossmatch group |
| n | How many signals in that group were tested |
| pass_rate | Fraction that passed |
| common_failures, vetoes | Which tests caught the most |

**What to expect:** `KNOWN_PLANET` high (~80 %), `KNOWN_FP` low. If `KNOWN_PLANET` drops a lot after a change, the vetting got too strict. If `KNOWN_FP` goes up, it got too loose.

### The benchmark report

In `docs/benchmarks/`. The main line is **Detectable recall**: out of every 100 known candidates that should be found in one sector, how many the system finds. Target: ≥ 90 %. The interval in parentheses (95 % CI) shows the uncertainty: with 135 objects, 91 % could actually be anything between 85 % and 95 %.

---

## 5. Three true stories from day one

These cases show why each stage exists.

**1. The invented planet.** The star HD 23472 has 5 known planets. In a single sector, the system saw one transit of planet b and one of planet c and concluded there was a 10.29-day planet. The period crossmatch didn't catch it, because 10.29 days is not the period of either one. We had to build **transit-by-transit** matching.

**2. The planet that looked like a binary.** WASP-18 b is a giant planet so hot that TESS sees its light disappear when it passes **behind** the star. The secondary eclipse test was vetoing it as a binary. The fix: only veto if the secondary drop is larger than 10 % of the main one, because planets produce small secondary drops.

**3. The best candidate that wasn't.** HD 271883 showed a clean 6.6-day signal: 4,900 ppm, passed every basic test, centroid on target, no known binary. But the star was observed in 10 sectors. If the signal were real, it should have shown up strongly in the others. It didn't. It was a single-sector glitch.

The general lesson: **an alert has to survive serious attempts to knock it down**.

---

## 6. How to use it day to day

```
uv sync                                     # installs everything (once)
uv run planethunter run-sector 70 --limit 2000
```

This command runs all 8 steps and prints a summary. To see the candidates and open dossiers:

```
uv run planethunter candidates
uv run planethunter dossier <signal_id>
```

To get alerts on Telegram, create a `.env` file in the project folder. Git already ignores it, so the token won't end up in the repository.

```
TG_TOKEN=your_bot_token
TG_CHAT_ID=your_chat_id
PLANETHUNTER_MAX_WORKERS=4
```

The last line is optional: it limits the analysis to 4 CPU cores (step 3). Put each setting on its own line, with no comments on the same line.

Then run with `--send`. Without `--send`, nothing is sent; the messages stay in `data/outbox/`.

**Where things live:**

| Folder | Contents |
|---|---|
| `data/parquet/` | Downloaded light curves |
| `data/mirrors/` | Catalog copies |
| `data/planethunter.duckdb` | Database with signals, vetting, candidates, alerts |
| `data/dossiers/` | HTML dossiers |
| `data/outbox/` | Simulated alerts |
| `config/thresholds.yaml` | All the thresholds. Each one has a comment explaining why it has that value. |

---

## 7. What to do with a P1 candidate

1. **Open the dossier** and go through section 4 of this guide. Any clear "bad sign": reject it.
2. **Open the star's page on ExoFOP** (link in the dossier). See whether anyone has commented on it.
3. **Search for the TIC on Google Scholar or ADS** (ui.adsabs.harvard.edu). There may be a recent paper that hasn't made it into the catalogs yet.
4. Record your decision: `uv run planethunter review <signal_id> approved` (or `rejected --reason eb`, `follow_up`; the rejection reasons are `eb`, `blend`, `systematic`, `noise`, `already_known` and `other`). Rejected signals leave the list; the decisions become examples for the system to learn from in the future.
5. If everything checks out, the path is to **submit it as a CTOI on ExoFOP**, with the dossier. The TESS team evaluates it and may promote it to a TOI. From there, other telescopes carry out follow-up observations.
6. **Never** announce it as a "discovery". The correct vocabulary is: signal, then candidate, CTOI, TOI, validated planet, confirmed planet. Each step requires more evidence, and the last ones require other telescopes.

---

## 8. What to study, in order

Full version, with beginner, intermediate and advanced levels, exercises and self-assessment: **[Study plan](STUDY_PLAN.md)**. Below is the summary.

Suggested track, from the most basic up to what you need to work on the algorithms. Each level has a concrete goal.

### Level 1. Concepts (1–2 weeks)

**Goal:** understand what a transit is, why the depth depends on size, and what an eclipsing binary is.

- NASA's exoplanet website, section on the transit method: science.nasa.gov/exoplanets
- Introductory videos on the "transit method" and "eclipsing binary" (any serious science-communication channel).
- **Highly recommended practice:** the Planet Hunters TESS project on the Zooniverse platform. You look at real light curves and mark transits. In a few hours your eye learns the difference between a transit, a binary and a glitch. Volunteers in that project have already had candidates promoted to planets.

### Level 2. TESS data (2–3 weeks)

**Goal:** open a light curve on your own and spot a known transit.

- The official tutorials of the **Lightkurve** library (lightkurve.github.io). Start with the tutorial on LightCurve objects and then the one on identifying transit signals. You'll download data, plot it, fold it on the period and find a known planet.
- The TESS guide on the HEASARC/NASA website: what sectors, cameras and cadences are.
- Exercise: run `uv run planethunter run-target 261136679` (the star Pi Mensae) and compare with the planet Pi Men c in the NASA Exoplanet Archive.

### Level 3. Signal search and basic statistics (3–4 weeks)

**Goal:** understand the periodogram, SDE, SNR, white noise and red noise.

- Statistics: mean, standard deviation, the normal distribution, what "3 sigma" means, the chi-squared test. Any introductory statistics course covers these.
- Paper: Hippke & Heller (2019), "Optimized transit detection algorithm to search for periodic transits of small planets", *Astronomy & Astrophysics* 623, A39. It describes the TLS the system uses. Read the introduction and figures; the equations can wait.
- The concept of **red noise**: noise that doesn't go away when you average. It explains why several tests in this project measure the noise in blocks.

### Level 4. False positives (3–4 weeks)

**Goal:** understand each vetting test and why it exists.

- Classic review: Winn (2010), "Transits and Occultations", freely available on arXiv (arXiv:1001.2010). It explains the physics of transits, duration, shape and secondary eclipses. It is the basis for the `duration`, `shape` and `secondary` tests.
- The TOI catalog paper: Guerrero et al. (2021), *The Astrophysical Journal Supplement* 254, 39. It shows how the TESS team does its own vetting.
- Giacalone et al. (2021), *The Astronomical Journal* 161, 24, on triceratops: how the false positive probability is computed.

### Level 5. Programming (alongside the others)

**Goal:** read and change the code.

- Basic Python, then **NumPy** and **pandas** (handling tables and arrays).
- Matplotlib for plots.
- Git, for versioning changes.

### How to know you've understood it

You understand the tool when you can, without help:

1. Open a dossier and say, by looking at the plots, whether it looks like a planet or a binary.
2. Explain why a 2 R⊕ planet around a large star is harder to find than around a red dwarf.
3. Say why the system requires at least 2 transits.
4. Explain what would happen if the detrending window were 0.2 days.

---

## 9. Honest limits

- **Finding a new planet is rare.** TESS and the community have already combed through the data many times. In the first batch of 2164 stars, the system produced 0 strong candidates after ruling everything out. That is expected, not a flaw.
- **Where the odds are better:** faint stars (Tmag 13.5–15) that the official pipelines give lower priority; long-period planets with one or two transits; additional planets in known systems. These niches are in the plan, and some of them are not implemented yet.
- **The system does not confirm planets.** Confirmation requires observations from other telescopes: radial velocity, high-resolution imaging, photometry in other colors.
- **Still missing:** search in full-frame images (fainter stars), a single-transit detector, completeness measurement by injecting synthetic transits, and a neural-network classifier. A simple statistical model (`calibrate`) already helps rank the queue, but it can only lower priority.

---

## 10. Frequently asked questions

**The system said P1. Did I find a planet?**
Not yet. P1 means the signal survived every automated test available. Follow section 7.

**Why so many "NEW" signals if almost none become candidates?**
`NEW` only means "not in any catalog". The vast majority are noise or glitches that no catalog records, precisely because they are nothing. That's what vetting is for.

**Why does the system discard signals with only one transit?**
Without at least two, the period is unknown, and a single event is easy for a glitch to imitate. Single transits are a valuable niche, but they need a dedicated detector, which is in the plan.

**Can I trust the score?**
It is a useful ranking, not a probability. A score of 1.0 says no automated test found a problem; it does not say it is a planet. The same goes for `p_rank`: it is learned from known planets and known false positives, and the planets you are looking for may not look like either.

**Why is the system slow sometimes?**
Downloading data is the slowest part (~4 minutes for 2000 stars). Deep vetting downloads pixel images and other sectors for each candidate.
