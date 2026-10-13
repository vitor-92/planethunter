# M4. TESS data in Python

<p class="meta">Intermediate level · weeks 6–8 · about 12 hours</p>

!!! abstract "In this lesson you will learn"
    - Search for and download a star's TESS light curve with the Lightkurve library.
    - Plot, clean and flatten the curve.
    - Run a BLS periodogram and recognize the true peak and the aliases.
    - Fold the curve at the period you found and see the transit.
    - Do three vetting tests by hand: odd/even, phase 0.5 and the search for a second signal.
    - Compare your result with PlanetHunter's for the same target.

!!! warning "Prerequisite: programming track"
    This lesson assumes you have finished [P1. Python basics](../programming/p1-python-basics.md) and [P2. NumPy, pandas and Matplotlib](../programming/p2-numpy-pandas-matplotlib.md). You need to know what a NumPy array is, how to call functions with keyword arguments and how to make a simple plot. The lesson [P3. Lightkurve in practice](../programming/p3-lightkurve-in-practice.md) complements this one, with more details about the library.

## The target: Pi Mensae c

**Pi Mensae** (TIC 261136679) is a Sun-like star, very bright (Tmag 5.1), in the southern sky. Its planet **Pi Men c** was one of the first announced with TESS data, in 2018: a period of about **6.27 days** and transits of about **300 ppm**, a little more than 2 Earth radii.

It is an ideal target to start with: the signal is real and known, but it is not obvious to the naked eye in the raw curve. You will need every step of the search to see it. We will use only **sector 1**, the first TESS sector (July and August 2018).

## Setup

Lightkurve already comes installed with PlanetHunter. In the project folder, create a file `pimen.py` (outside `src/`, for example in a `studies/` folder of your own) and run each block with:

```bash
uv run python pimen.py
```

If you prefer Jupyter, paste the blocks into cells, in order. The plots appear on their own; in a script, use `plt.show()` at the end of each plot, as in the code below.

The first download needs internet and takes a few seconds. Lightkurve keeps the files in a local cache and does not download them again.

## Step 1. Search

```python
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
import lightkurve as lk

# Search the MAST archive for all 2-minute (120 s) SPOC light curves of this star.
search_all = lk.search_lightcurve(
    "TIC 261136679", mission="TESS", author="SPOC", exptime=120
)
print(search_all)  # one row per sector

# Now only sector 1.
search = lk.search_lightcurve(
    "TIC 261136679", mission="TESS", author="SPOC", exptime=120, sector=1
)
print(search)
```

**What you should see.** The first table has more than twenty rows: Pi Mensae lies near the south ecliptic pole and was observed in many sectors between 2018 and 2025. Each row has the mission and sector, the year, the author (SPOC), the exposure time (120 s) and the target name. The second table has a single row: `TESS Sector 01 2018 SPOC 120 261136679`.

!!! note "Why 2-minute SPOC"
    SPOC is the mission's official pipeline, which produces curves for preselected targets at a 2-minute cadence. It is the same kind of data PlanetHunter ingests by default. The curve already comes corrected for telescope effects (the PDCSAP column) and for contamination by neighboring stars.

## Step 2. Download and inspect

```python
lc = search.download()  # TessLightCurve object

# Header metadata: brightness, temperature and radius of the star (from the TIC).
print(lc.meta["OBJECT"], "sector", lc.meta["SECTOR"])
print("Tmag", lc.meta["TESSMAG"], "Teff", lc.meta["TEFF"], "R*", lc.meta["RADIUS"])
print("columns:", lc.colnames[:8])
print(len(lc), "points, from", lc.time.min(), "to", lc.time.max())
```

**What you should see.** `TIC 261136679 sector 1`, Tmag 5.105, Teff about 5,990 K, radius 1.149 R☉. About 18,264 points, from BTJD 1325.30 to 1353.18. BTJD is TESS time: days since a reference date.

By default, Lightkurve uses the `pdcsap_flux` column as `flux` and already discards the cadences the telescope flagged as bad ("default" quality mask, the same one PlanetHunter uses).

## Step 3. Plot the raw curve

```python
lc = lc.remove_nans().normalize()  # drop empty points and divide by the median (normal brightness = 1)
ax = lc.plot()
ax.set_title("Pi Mensae, sector 1, normalized curve")
plt.show()
```

**What you should see.**

- A band of points between about 0.9997 and 1.0003, that is, ±300 ppm.
- A **gap** near BTJD 1339: the pause to send data to Earth, between the sector's two orbits.
- A noisier stretch around BTJD 1347 to 1349.
- The transits are there, but you can barely tell them apart from the noise. If you look carefully, near 1325.5, 1331.8, 1338.0, 1344.3 and 1350.6 there are subtle dips. Without knowing where to look, you would not find them.

This is the typical situation: the signal is below the noise of each point. The statistics from lesson [M1](m1-statistics-for-signals.md) are what will reveal it.

## Step 4. Clean and flatten

```python
# Remove only outliers going UP (flares). Never down: that would erase transits.
clean = lc.remove_outliers(sigma_upper=4, sigma_lower=np.inf)

# Flatten: estimate the slow trend and divide by it.
# window_length is in number of points and must be odd: 721 x 2 min = 1 day.
flat, trend = clean.flatten(window_length=721, return_trend=True)

ax = clean.plot(label="clean")
trend.plot(ax=ax, color="red", label="trend")
plt.show()

noise_ppm = np.std(flat.flux.value) * 1e6
print(f"{len(clean)} points; noise per point: {noise_ppm:.0f} ppm")
```

**What you should see.** About 9 points removed (18,255 left). The red trend is almost straight: Pi Mensae is a quiet star. The noise per point comes out at about **128 ppm** (the robust sigma, via the MAD, gives about 120 ppm).

!!! info "Same idea, different filter"
    Lightkurve's `flatten` uses a Savitzky-Golay filter. PlanetHunter uses wotan's **biweight**, which is more robust to transits inside the window. Both use a 1-day window here, for the reasons in lesson [M3](m3-periodograms.md): anything shorter eats long transits.

## Step 5. BLS periodogram

```python
periods = np.linspace(1, 15, 20000)              # days
durations = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]  # days (1.2 h to 4.8 h)
bls = flat.to_periodogram(method="bls", period=periods, duration=durations)

bls.plot()
plt.show()

P = bls.period_at_max_power
t0 = bls.transit_time_at_max_power  # Time object; .value gives the number in BTJD
dur = bls.duration_at_max_power
depth = bls.depth_at_max_power
print(f"P = {P:.4f}, t0 = {t0.value:.3f}, duration = {dur:.2f}, depth = {depth.value * 1e6:.0f} ppm")

# Peak prominence, in the spirit of the SDE: how many standard deviations above the mean.
prominence = (bls.max_power - np.mean(bls.power)) / np.std(bls.power)
print(f"peak prominence: {prominence:.1f}")
```

**What you should see.**

- A dominant peak at **6.27 d**, with power near 1,400.
- Smaller peaks, the **aliases**: 12.53 d (2P, power ~860), 3.13 d (P/2, ~750) and others at 9.4 d (3P/2), 4.18 d (2P/3) and 2.09 d (P/3).
- Output: `P = 6.2664 d, t0 = 1325.507, duration = 0.12 d, depth = 228 ppm`.
- Peak prominence: about **12.9**.

The duration of 0.12 d (2.9 h) is the closest value in the **grid** you gave. With a finer grid, the result would change a little. The prominence is not TLS's SDE (the definitions of power differ), but the idea is the same.

## Step 6. Fold and see the transit

```python
folded = flat.fold(period=P, epoch_time=t0)  # time becomes "days since the transit"

ax = folded.scatter(alpha=0.3, s=2, label="2-min points")
folded.bin(time_bin_size=10 * u.min).scatter(ax=ax, color="red", s=20, label="10-min average")
ax.set_xlim(-0.3, 0.3)
plt.show()
```

**What you should see.** A wide gray cloud and, on top of it, the red points forming a clear **U**: a step of about 250 ppm between −0.06 and +0.06 day. The five transits, invisible one by one, add up to a sharp signal. This is the $\sqrt{N}$ from lesson M1 in action.

Compare the shape with lesson [M2](m2-transit-physics.md): short ramps and a wide bottom. No V.

## Step 7. Three vetting tests by hand

```python
stats = bls.compute_stats(period=P, duration=dur, transit_time=t0)
print("transits:", stats["transit_times"])
print("points per transit:", stats["per_transit_count"])
print("odd:", stats["depth_odd"], "even:", stats["depth_even"])
print("at phase 0.5:", stats["depth_phased"])
print("if the period were P/2:", stats["depth_half"])

# Search for a second signal: mask the transits and run BLS again.
mask = bls.get_transit_mask(period=P, transit_time=t0, duration=2 * dur)
rest = flat[~mask]
bls2 = rest.to_periodogram(method="bls", period=periods, duration=durations)
prominence2 = (bls2.max_power - np.mean(bls2.power)) / np.std(bls2.power)
print(f"2nd signal: P = {bls2.period_at_max_power:.3f}, "
      f"{bls2.depth_at_max_power.value * 1e6:.0f} ppm, prominence {prominence2:.1f}")
```

**What you should see.** The depths come out as (value, error) pairs as a fraction of the brightness: `0.00022391` means 224 ppm.

- Five transits (1325.51; 1331.77; 1338.04; 1344.31; 1350.57), with 81 to 87 points each.
- Odd: 224 ± 7 ppm. Even: 231 ± 6 ppm. **Equal within the error.**
- Phase 0.5: −10 ± 5 ppm. **No secondary eclipse.**
- Depth with P/2: 126 ppm, half, as predicted for an alias (lesson M3).
- Second signal: something near 7 d with 37 ppm and a prominence of about 4. **Nothing.** Only one planet transits in sector 1.

You have just done, with your own hands, PlanetHunter's `odd_even` and `secondary` tests and its iterative search.

!!! example "Exercise 1"
    Calculate the significance of the odd/even difference, in sigmas, the way the `odd_even` test does. Would it fail?

    ??? success "Show answer"
        Difference: 231 − 224 = 7 ppm. Combined error: $\sqrt{7^2 + 6^2} = \sqrt{85} \approx 9.2$ ppm. Significance: 7/9.2 ≈ **0.8 sigma**.

        The test fails from 3 sigma and vetoes from 5. It passes comfortably. The odd and even transits are equal, as you would expect from a planet.

!!! example "Exercise 2"
    Use the depth and the star's radius to estimate the radius of Pi Men c in Earth radii. Do the calculation twice: with the BLS depth (228 ppm) and with PlanetHunter's trapezoid depth (272 ppm). Given: 1 R☉ = 109.1 R⊕.

    ??? success "Show answer"
        $R_p = \sqrt{\delta} \times R_\star \times 109.1$.

        With 228 ppm: $\sqrt{0.000228} = 0.0151$. $0.0151 \times 1.149 \times 109.1 \approx$ **1.9 R⊕**.

        With 272 ppm: $\sqrt{0.000272} = 0.0165$. $0.0165 \times 1.149 \times 109.1 \approx$ **2.1 R⊕**, the value that appears in PlanetHunter's `radius` test.

        The difference comes from the model: the box averages in the ramps and underestimates the depth (lesson M2). A 20% error in the depth becomes 10% in the radius, because the radius goes with the square root.

## Step 8. Compare with PlanetHunter

Now run the same target in the tool, with sector 1 only:

```bash
uv run planethunter run-target 261136679 --sectors 1
```

The command downloads the sector, runs the search (TLS with the detrending variants), the crossmatch and the basic vetting, and prints the `run_id`, a table of signals with the `signal_id`, and the path to the dossier for each strong signal. With the catalog mirrors up to date, the 6.27 d signal should show up as `KNOWN_PLANET`, matched to Pi Men c. If you see a `WARNING: mirrors missing or stale`, run `uv run planethunter mirrors sync` first.

!!! warning "Do not forget `--sectors 1`"
    Without it, the command downloads **all** of the star's sectors (more than twenty) and does a multi-sector search. It takes much longer and the numbers change (more transits, higher SNR). Watch out: sectors you have already downloaded before go into the search even with `--sectors 1`.

The last lines of the output show the dossier for each strong signal, for example `dossier for signal 1234: data/dossiers/tic261136679_sig1234.html`. Open it in your browser. To generate it again later, use `uv run planethunter dossier <signal_id>`.

### What to expect

We ran PlanetHunter's search and vetting code on sector 1 of Pi Mensae on 2026-10-09. The table compares it with what you got in this lesson:

| | Lightkurve (this lesson) | PlanetHunter |
|---|---|---|
| Cleaning | NaN and points 4σ above | quality mask, 4σ above before and after flattening |
| Flattening | Savitzky-Golay, 1 d | biweight (wotan), 1.0 d, segments separated at the gaps |
| Search | BLS, 1 to 15 d, 6 durations | TLS, 0.5 to ~25 d (0.9 × data span), fine grid, points binned to 10 min |
| Period | 6.266 d | 6.269 d |
| Time of 1st transit (BTJD) | 1325.507 | 1325.503 |
| Duration | 2.9 h (grid value) | 3.08 h (TLS); 3.11 h (trapezoid) |
| Depth | 228 ppm (box) | 287 ppm (TLS); 272 ppm (trapezoid) |
| Peak strength | prominence 12.9 | SDE 19.0 |
| SNR | ~37 (calculation from lesson M1) | 33.6 |
| Transits | 5 | 5 |
| Odd / even | 224 / 231 ppm | 284 / 259 ppm (1.1σ) |
| Phase 0.5 | −10 ppm | −9 ppm |

PlanetHunter's full basic vetting gave **score 1.0, PASS_BASIC**: radius 2.1 R⊕; duration 3.11 h against 3.79 h predicted (ratio 0.82, lesson M2); $\tau/T_{14}$ = 0.11 (U shape); centroid with implied source 0.15 pixel from the target; 40% of transits at segment edges (2 of 5, below the 50% limit); consistency between transits with p = 0.62.

The numbers in your dossier may differ a little if the pipeline version or the TIC parameters change. Since 2026-10-10 the search also covers a different period range (from about 0.2–0.3 d; before, TLS's own default really stopped it at half the data span, about 14 d here), and PlanetHunter measures the duration and the SNR itself instead of copying them from TLS (lesson [M3](m3-periodograms.md)), so those two rows will change slightly in a new run. The dossier's **Provenance** section records the `run_id`, the version and the window used in each sector.

!!! tip "In the tool"
    Each step in this lesson has an equivalent in the code: cleaning and flattening in `src/planethunter/preprocess/clean.py`; search in `src/planethunter/search/tls.py`; odd/even, phase 0.5, shape and the other tests in `src/planethunter/vetting/basic.py`. In the dossier, the **Folded transit** plot corresponds to your step 6, and the **Odd, even and secondary** panel to step 7.

!!! example "Exercise 3"
    In the table, PlanetHunter has SDE 19.0 and your "prominence" came out at 12.9. Give two reasons for the difference.

    ??? success "Show answer"
        1. **Model.** TLS uses a realistic transit, with ramps and limb darkening; BLS uses a box. The better model fits more of the signal, and the peak grows.
        2. **Definition and grid.** TLS's SDE is computed on a different quantity (the SR, normalized) and over a different period grid (from 0.5 to ~25 d, with a density chosen by `oversampling_factor`). Your prominence uses the BLS power from 1 to 15 d. The periodogram's mean and standard deviation change with the grid.

        Cleaning details also count (the biweight filter, segments separated at the gaps), as does the 10-minute binning. The two numbers are not directly comparable; what matters is that both methods find the same period, comfortably.

!!! example "Exercise 4 (challenge)"
    Choose another sector from the list in step 1 and repeat the whole lesson, changing `sector=1`. Do the period and the depth match? How many transits do you see?

    ??? success "Show answer"
        The period should match 6.27 d within the uncertainty (which, with a single sector, is a few thousandths of a day), and the depth should match sector 1 within a few tens of ppm. The number of transits depends on where that sector's gaps fall: with ~27 days and a period of 6.27 d, expect 4 or 5. If a sector gives a very different result, look at the curve: bigger gaps, noisy stretches or a transit at an edge explain most cases. It is the same reasoning as the other-sectors test in the deep vetting.

## Lesson checklist

- [ ] I searched for and downloaded the sector 1 curve of Pi Mensae with Lightkurve.
- [ ] I plotted the raw curve and found the gap in the middle of the sector.
- [ ] I cleaned only upward and flattened with a 1-day window, knowing why.
- [ ] I ran BLS and found 6.27 d; I identified at least two aliases in the periodogram.
- [ ] I folded the curve and saw the U-shaped transit.
- [ ] I did the odd/even and phase 0.5 tests and the search for a second signal by hand.
- [ ] I ran `planethunter run-target 261136679 --sectors 1`, opened the generated dossier and compared it with the table in this lesson.

## Going further

- Official Lightkurve tutorials ([lightkurve.github.io](https://lightkurve.github.io/lightkurve/)): start with "LightCurve objects" and then the tutorial on identifying transiting signals with BLS.
- Pi Mensae's page on ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/target.php?id=261136679)): star parameters, TOIs and community notes.
- Huang et al. (2018), *The Astrophysical Journal Letters* 868, L39: the paper announcing Pi Men c with TESS data. Look at the figures and compare them with your folded transit.
- Introductory documentation for NumPy ([numpy.org](https://numpy.org/doc/stable/user/absolute_beginners.html)) and pandas ([pandas.pydata.org](https://pandas.pydata.org/docs/getting_started/index.html)), if any part of the code looked strange.
