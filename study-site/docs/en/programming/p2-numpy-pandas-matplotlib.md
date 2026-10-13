# P2. NumPy, pandas and Matplotlib

<p class="meta">Programming track · after the basic level, before M4 · about 12 hours</p>

!!! abstract "In this lesson you will learn"
    - Use NumPy arrays to do calculations on thousands of points at once.
    - Simulate a light curve with noise and a box-shaped transit, and measure the depth.
    - Read the ExoFOP TOI table with pandas, filter it and summarize it.
    - Make plots with Matplotlib: light curve, curve folded on the period and a period versus radius diagram.

Prerequisite: [lesson P1](p1-python-basics.md). In the study folder, install the libraries (if you have not done so yet):

```powershell
uv add numpy pandas matplotlib
```

## NumPy: calculations with many numbers at once

A TESS light curve has about 20,000 measurements per sector. Doing calculations with a `for` loop, point by point, is slow and wordy. **NumPy** solves this with the **array**: a sequence of numbers of the same type in which each operation applies to all elements at the same time. This is called a **vectorized operation**.

```python
import numpy as np

d_ppm = np.array([84, 1251, 10090])      # Earth, Neptune, Jupiter in front of the Sun
print(d_ppm / 1e6)                       # divides all three at once
print(np.sqrt(d_ppm / 1e6) * 109.1)      # radii in R_earth: ~[1, 3.9, 11]
```

With an ordinary list, `my_list / 1e6` gives an error. With an array, it works. That is the most important difference between the two.

Other tools you will use all the time:

| Code | What it does |
|---|---|
| `np.arange(0, 27, 0.5)` | Numbers from 0 up to (not including) 27, in steps of 0.5 |
| `np.median(a)`, `np.mean(a)`, `np.std(a)` | Median, mean and standard deviation |
| `a > 1.0` | Array of `True`/`False`, a **mask** |
| `a[mask]` | Only the elements where the mask is `True` |
| `np.abs(a)` | Absolute value of each element |

## Simulating a light curve

Let us build a light curve with a known transit. That way you know the right answer and can test whether your measurement recovers it. It is the same idea as the transit injection test the project uses to measure itself (lesson A5).

Create the file `simulate.py`:

```python
"""Simulates 27 days of TESS (2-min cadence) with a box transit and noise."""
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(seed=42)   # random number generator, always the same

# 1. Time axis: one 27-day sector, one point every 2 minutes
cadence_days = 2 / (60 * 24)
time = np.arange(0.0, 27.0, cadence_days)
print("points:", time.size)            # 19440

# 2. Parameters of the made-up planet
period = 3.0             # days
t0 = 1.5                 # time of the first transit, days
duration_hours = 3.0
depth_ppm = 5000.0
noise_ppm = 1000.0       # scatter of each measurement

# 3. Phase: distance from each point to the nearest transit, in days
phase = (time - t0 + 0.5 * period) % period - 0.5 * period
in_transit = np.abs(phase) < (duration_hours / 24) / 2

# 4. Box model: brightness 1 outside the transit, 1 - depth inside
model = np.ones_like(time)
model[in_transit] = 1.0 - depth_ppm / 1e6

# 5. Gaussian noise added to the model
noise = rng.normal(loc=0.0, scale=noise_ppm / 1e6, size=time.size)
flux = model + noise
```

Step 3 is the heart of the simulation. The `%` operator gives the remainder of a division. It "wraps" time into laps of one period, like a clock that goes back to zero every 3 days. Adding and subtracting half a period centers the transit at phase zero. The resulting `phase` goes from −1.5 to +1.5 days.

Step 5 uses **Gaussian noise** (normal distribution, lesson M1): each measurement is off by a little, up or down, with a standard deviation of 1,000 ppm.

### Measuring the depth

Now pretend you do not know the answer. Compare the typical brightness inside and outside the transit. Use the **median**, which is less sensitive to odd points than the mean.

```python
level_out = np.median(flux[~in_transit])    # ~ means "not"
level_in = np.median(flux[in_transit])
measured_depth = (1 - level_in / level_out) * 1e6
n_in = in_transit.sum()                     # True counts as 1
snr = measured_depth / (noise_ppm / np.sqrt(n_in))

print(f"points in transit: {n_in}")         # 801
print(f"measured depth: {measured_depth:.0f} ppm (true: 5000)")   # ~4975
print(f"approximate SNR: {snr:.0f}")        # ~141
```

Why divide the noise by $\sqrt{N}$? When you average $N$ independent measurements, the error of the mean drops with the square root of $N$. With 801 points in transit, the effective noise drops from 1,000 to about 35 ppm. A 5,000 ppm dip sits far above that. This is a simplified version of the **signal-to-noise ratio** (SNR) that PlanetHunter requires to be at least 7.1 (lesson M1).

## Matplotlib: looking at the data

**Matplotlib** draws plots. Continue in the same file:

```python
fig, axes = plt.subplots(2, 1, figsize=(10, 7))

# Top panel: the whole light curve
axes[0].plot(time, flux, ".", markersize=1, color="0.5")
axes[0].set_xlabel("time (days)")
axes[0].set_ylabel("relative brightness")
axes[0].set_title("Simulated light curve")

# Bottom panel: folded curve (all transits on top of each other)
phase_hours = phase * 24
axes[1].plot(phase_hours, flux, ".", markersize=1, color="0.7", label="measurements")

# Averages in 15-minute bins, to see the shape
edges = np.linspace(-36, 36, 289)                # 288 bins of 0.25 h
idx = np.digitize(phase_hours, edges) - 1        # which bin each point falls into
total = np.bincount(idx, weights=flux, minlength=288)
count = np.bincount(idx, minlength=288)
centers = 0.5 * (edges[:-1] + edges[1:])
axes[1].plot(centers, total / count, "o", color="C3", label="15-min average")

axes[1].set_xlim(-6, 6)
axes[1].set_xlabel("hours from the center of the transit")
axes[1].set_ylabel("relative brightness")
axes[1].legend()

fig.tight_layout()
plt.show()
```

Run it with `uv run python simulate.py`. In the top panel, the transit almost disappears in the noise. In the bottom one, after **folding** the curve on the period, the 9 transits stack up and the box shows up clearly. This is what the PlanetHunter dossier shows in the "Folded transit" section.

`np.bincount` adds up the fluxes in each bin at once, with no loop. Dividing the sum by the count gives the average per bin.

!!! info "Why folding works"
    Folding on the right period puts all the transits in the same place. The noise, which is random, cancels out in the average. The transit, which repeats, adds up. Folding on the wrong period spreads the transits out and the box disappears. A periodogram (lesson M3) is, at heart, testing thousands of foldings and seeing which one makes the box deepest.

## pandas: tables

**pandas** works with tables, called **DataFrames**: rows and named columns, like a spreadsheet you control with code.

### Reading the ExoFOP TOI list

ExoFOP publishes the list of all TOIs (official TESS candidates) as a CSV file, a text file with comma-separated values. pandas reads it straight from the internet:

```python
import pandas as pd

URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
tois = pd.read_csv(URL, low_memory=False)
tois.to_csv("tois.csv", index=False)     # keeps a local copy
print(tois.shape)                        # (rows, columns)
```

Next time, read the local copy with `pd.read_csv("tois.csv")`. It is faster and spares the ExoFOP server.

On October 9, 2026 the table had 8,151 rows and 63 columns. Your numbers will be larger: the list grows every week.

### Looking at and selecting columns

```python
columns = ["TOI", "TIC ID", "TFOPWG Disposition", "Period (days)",
           "Depth (ppm)", "Planet Radius (R_Earth)"]
print(tois[columns].head())             # the first 5 rows
print(tois["TFOPWG Disposition"].value_counts(dropna=False))
```

`value_counts` counts how many times each value appears. The `TFOPWG Disposition` column holds the decision of the TESS follow-up group:

| Code | Meaning | On 2026-10-09 |
|---|---|---|
| PC | Planet candidate | 4,820 |
| FP | False positive | 1,315 |
| CP | Confirmed planet (found by TESS) | 815 |
| KP | Planet already known before TESS | 606 |
| APC | Ambiguous candidate | 490 |
| FA | False alarm | 100 |

### Filtering

Filtering in pandas means using a mask, just like in NumPy:

```python
# Confirmed or known planets
planets = tois[tois["TFOPWG Disposition"].isin(["CP", "KP"])]

# Of those, the ones with a period shorter than 1 day, from deepest to shallowest
short = planets[planets["Period (days)"] < 1.0]
print(len(planets), len(short))         # 1421 and 78 on 2026-10-09
print(short.sort_values("Depth (ppm)", ascending=False)[columns].head(8))

# A specific target: WASP-18, TIC 100100827
wasp18 = tois[tois["TIC ID"] == 100100827]
print(wasp18[["TOI", "TFOPWG Disposition", "Period (days)", "Depth (ppm)",
              "Duration (hours)", "Planet Radius (R_Earth)", "Sectors"]])
```

WASP-18 b shows up as TOI-185.01, disposition KP, period 0.941453 day, depth 11,445 ppm, duration 2.05 hours, radius 15.3 R⊕, observed in sectors 2, 3, 29, 30 and 69. You will measure these numbers yourself in [lesson P3](p3-lightkurve-in-practice.md).

To combine conditions, use `&` (and) and `|` (or), with each condition in parentheses:

```python
small = planets[(planets["Planet Radius (R_Earth)"] < 2) &
                (planets["Period (days)"] < 10)]
```

### Statistics and groups

```python
print(planets["Period (days)"].describe())   # count, mean, quartiles...
print(tois.groupby("TFOPWG Disposition")["Planet Radius (R_Earth)"].median())
```

`describe` shows that the median period of the CP and KP planets is about 4.3 days. The TESS search favors short periods: with only 27 days per sector, a 4-day planet transits several times, a 40-day one maybe only once.

`groupby` splits the table by disposition and computes the median radius in each group. On 2026-10-09, the CPs had a median of 3.2 R⊕, and the FPs, 10.0 R⊕. False positives tend to look "big", because many are eclipsing binaries with deep dips.

### Period versus radius plot

```python
fig, ax = plt.subplots(figsize=(8, 6))
for disp, color in [("PC", "0.7"), ("FP", "C3"), ("CP", "C0"), ("KP", "C2")]:
    group = tois[tois["TFOPWG Disposition"] == disp]
    ax.scatter(group["Period (days)"], group["Planet Radius (R_Earth)"],
               s=4, color=color, label=f"{disp} ({len(group)})")
ax.set_xscale("log")      # logarithmic scale: 1, 10, 100 get the same space
ax.set_yscale("log")
ax.set_xlabel("period (days)")
ax.set_ylabel("radius (R_earth)")
ax.legend()
plt.show()
```

The **logarithmic scale** gives the same space to "from 1 to 10" and "from 10 to 100". Without it, almost all the points would be squeezed into a corner.

!!! tip "In the tool"
    PlanetHunter reads exactly this ExoFOP CSV, with the same columns (`TFOPWG Disposition`, `Period (days)`, `Epoch (BJD)`). See `normalize_exofop_toi` in `src/planethunter/catalogs/mirrors.py`, which builds the local mirror used in the crossmatch, and `build` in `src/planethunter/benchmark.py`, which picks the TOIs of a sector with `str.split(",")` on the `Sectors` column, as in exercise 2 below. Light curves are stored as NumPy `float32` arrays (time in `float64`), and almost every function in the pipeline takes and returns DataFrames.

## Exercises

!!! example "Exercise 1. An Earth in the noise"
    In `simulate.py`, change the depth to 84 ppm (Earth in front of the Sun) and keep the noise at 1,000 ppm. Compute the SNR. Would the planet be detected by the SNR ≥ 7.1 criterion? And with 500 ppm?

    ??? success "Show answer"
        With the same 801 points in transit, the effective noise is $1000/\sqrt{801} \approx 35$ ppm.

        - 84 ppm: SNR $\approx 84/35 \approx 2.4$. It does not pass. An Earth in a single sector, with this noise, stays hidden.
        - 500 ppm: SNR $\approx 14$. It passes comfortably.

        The measured values vary a little, because the noise is random. For an Earth to show up, you need less noise (a brighter star), more transits (several sectors) or a smaller star, which makes the dip deeper.

!!! example "Exercise 2. TOIs in sector 69"
    The `Sectors` column is a text like `"2,3,29,30,69"`. Select the TOIs observed in sector 69 and count them by disposition.

    ??? success "Show answer"
        ```python
        lists = tois["Sectors"].fillna("").astype(str).str.split(",")
        in_69 = lists.apply(lambda xs: "69" in [x.strip() for x in xs])
        s69 = tois[in_69]
        print(len(s69))
        print(s69["TFOPWG Disposition"].value_counts(dropna=False))
        ```
        `str.split(",")` turns each text into a list. `apply` runs a small function (`lambda`) on each row. Looking for `"69"` inside the list avoids confusing 69 with 169. On 2026-10-09 there were 407 TOIs: 260 PC, 74 CP, 37 FP, 22 KP, 13 APC, 1 FA. Do not use `str.contains("69")`: it would accept a sector 169 in the future.

!!! example "Exercise 3. Folding on the wrong period"
    In the simulation, fold the curve at 6 days (double) and at 1.5 days (half) instead of 3. Measure the depth at the center in each case. What happens?

    ??? success "Show answer"
        ```python
        for p in (6.0, 1.5):
            f = (time - t0 + 0.5 * p) % p - 0.5 * p
            inside = np.abs(f) < (duration_hours / 24) / 2
            print(p, (1 - np.median(flux[inside])) * 1e6)
        ```
        - At 6 days (2P), the center still shows about 5,000 ppm, but only half of the transits are there. The other half fall at phase ±3 days, "phase 0.5". Visually it looks like a binary with two equal eclipses.
        - At 1.5 days (P/2), half of the "windows" at phase zero have no transit. The measured depth drops to about 2,500 ppm, half.

        That is why aliases like $2P$ and $P/2$ are misleading (lesson M3), and why the vetting compares odd and even transits (lesson M5).

## Lesson checklist

- [ ] I did calculations with arrays without using loops
- [ ] I simulated a curve with a transit and recovered the depth
- [ ] I computed an approximate SNR and understood the role of $\sqrt{N}$
- [ ] I plotted the curve and the folded curve with binned averages
- [ ] I read the TOI CSV, filtered by disposition and period and found WASP-18 b
- [ ] I used `describe` and `groupby`
- [ ] I made the period versus radius diagram on a logarithmic scale
- [ ] I solved the three exercises

## Going further

- NumPy, absolute beginner's guide ([numpy.org](https://numpy.org/doc/stable/user/absolute_beginners.html)). Explains arrays, masks and vectorized operations at a calm pace.
- pandas, "10 minutes to pandas" ([pandas.pydata.org](https://pandas.pydata.org/docs/user_guide/10min.html)). A quick tour of reading, selecting, filtering and grouping.
- ExoFOP TOI download page ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/view_toi.php)). Shows the same table in the browser, useful for checking your filters.
- Curso em Vídeo — Python, world 3 (Gustavo Guanabara). Reinforces lists, dictionaries and functions, the foundation for using NumPy and pandas well (in Portuguese).
