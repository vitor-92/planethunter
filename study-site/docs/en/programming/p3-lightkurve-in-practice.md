# P3. Lightkurve in practice

<p class="meta">Programming track · alongside module M4 · about 10 hours</p>

!!! abstract "In this lesson you will learn"
    - Search for and download real TESS light curves with the Lightkurve library.
    - Clean, flatten, find the period with BLS and fold the curve.
    - Measure the transit depth and estimate the planet's radius.
    - Open the Parquet files PlanetHunter writes and query the DuckDB database with SQL.

Prerequisites: [P2](p2-numpy-pandas-matplotlib.md) and [lesson M3](../intermediate/m3-periodograms.md) on periodograms. This lesson is the hands-on part of [lesson M4](../intermediate/m4-tess-data-in-python.md). You will need an internet connection. In the study folder:

```powershell
uv add lightkurve pyarrow duckdb
```

## The target: WASP-18 b

We will work with **WASP-18 b**, a very hot giant planet hugging its star.

| Item | Value (ExoFOP, TOI-185.01) |
|---|---|
| Star | WASP-18, TIC 100100827, Tmag 8.83, radius 1.35 R☉ |
| Period | 0.941453 day (22.6 hours) |
| Depth | 11,445 ppm (about 1 %) |
| Duration | 2.05 hours |
| Disposition | KP (planet known before TESS) |

It is a great target for learning: the transit is deep and the period short. More than 20 transits fit in a 27-day sector. It also shows up in one of the project's real stories: PlanetHunter once mistook it for an eclipsing binary (guide, section 5).

Put the blocks from sections 1 to 5 together, in order, in a file called `wasp18.py` and run it with `uv run python wasp18.py`.

## 1. Search

```python
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np

search = lk.search_lightcurve("TIC 100100827", mission="TESS",
                              author="SPOC", exptime=120)
print(search)
```

`search_lightcurve` asks **MAST**, the public archive of TESS data, which curves exist. The filters ask for curves from **SPOC** (NASA's official pipeline) with a 120-second cadence. In October 2026 the answer had 10 rows: sectors 2, 3, 29, 30, 69, 96, 103, 104, 105 and 106.

When you import Lightkurve, a warning about `oktopus` may appear. You can ignore it: it is an optional module we do not use.

## 2. Download sector 69

```python
search69 = lk.search_lightcurve("TIC 100100827", author="SPOC",
                                exptime=120, sector=69)
lc_raw = search69.download()     # downloads and caches it on your disk
print(len(lc_raw))               # 16499 measurements
print(lc_raw.time[:3])           # time in BTJD
print(lc_raw.flux.unit)          # electron / s
print(lc_raw.meta["RADIUS"], lc_raw.meta["TESSMAG"], lc_raw.meta["TEFF"])
lc_raw.plot()
```

`download()` returns a **LightCurve** object: a table with `time` (time in BTJD), `flux` (brightness in electrons per second, already corrected by SPOC, the so-called PDCSAP) and `flux_err` (the error of each measurement). The `meta` dictionary holds the file header, with data about the star: radius 1.3466 R☉, Tmag 8.83, temperature 6,226 K.

By default, `download()` already discards measurements that TESS flagged as bad, such as those from pointing adjustments ("momentum dumps").

## 3. Clean

```python
lc = lc_raw.remove_nans().normalize()
lc = lc.remove_outliers(sigma_upper=4, sigma_lower=np.inf)
print(len(lc))                    # 14665
```

- `remove_nans()` drops empty measurements (NaN means "not a number").
- `normalize()` divides by the median brightness. The flux then sits around 1, and a dip of 0.01 means 1 %.
- `remove_outliers` cuts points more than 4 standard deviations **above** the curve. `sigma_lower=np.inf` turns off the cut on the low side. Cutting low points would erase the transits themselves. PlanetHunter does the same: `sigma_upper: 4.0` in `config/thresholds.yaml`.

## 4. Flatten and find the period with BLS

The star varies a little over the days. **Flattening** (or detrending) estimates this slow variation and divides by it. The `window_length` parameter is the size of the window, in number of measurements, and it must be odd. With 901 two-minute measurements, the window is 30 hours long, much longer than the 2-hour transit.

We do it in two passes. The first finds the transits roughly. The second redoes the flattening while **hiding** the transits, so the filter does not "eat" part of the dip.

```python
periods = np.linspace(0.5, 10, 20000)        # periods tested, in days
durations = [0.04, 0.06, 0.08, 0.10, 0.12]   # durations tested, in days

# Pass 1
pg1 = lc.flatten(window_length=901).to_periodogram(
    method="bls", period=periods, duration=durations)
P = float(pg1.period_at_max_power.value)
T0 = float(pg1.transit_time_at_max_power.value)
D = float(pg1.duration_at_max_power.value)

# Pass 2: mask the transits and flatten again
mask = lc.create_transit_mask(period=P, transit_time=T0, duration=1.5 * D)
flat = lc.flatten(window_length=901, mask=mask)
pg = flat.to_periodogram(method="bls", period=periods, duration=durations)
P = float(pg.period_at_max_power.value)
T0 = float(pg.transit_time_at_max_power.value)
D = float(pg.duration_at_max_power.value)
print(f"P = {P:.5f} d   T0 = {T0:.4f} BTJD   duration = {D * 24:.1f} h")
pg.plot()
```

**BLS** (Box Least Squares) tests each period and each duration in the list, fits a box to the folded data and measures how much of the dip it explains. The result is a **periodogram** with a peak at the right period (lesson M3). Output:

```text
P = 0.94130 d   T0 = 3182.7619 BTJD   duration = 1.9 h
```

The period matches ExoFOP's up to the third decimal place. The difference in the fourth comes from the grid: 20,000 periods between 0.5 and 10 days have a step of 0.0005 day.

!!! note "Why `float(...)`?"
    Lightkurve returns results as quantities with units (days) and, in recent Astropy versions, with a built-in "mask". `float(x.value)` turns everything into a plain number. Without it, `create_transit_mask` raises an error (`TypeError: cannot write to unmasked output`) with Lightkurve 2.6 and Astropy 8.

## 5. Fold and measure

```python
folded = flat.fold(period=P, epoch_time=T0)
phase = np.asarray(folded.time.value, dtype=float)    # days from the center
flux = np.asarray(folded.flux.value, dtype=float)

inside = np.abs(phase) < 0.25 * D     # core of the transit
outside = np.abs(phase) > 1.0 * D     # well away from the transit
level = np.median(flux[outside])
depth_ppm = (level - np.median(flux[inside])) * 1e6
noise_ppm = np.std(flux[outside]) * 1e6

R_star = lc.meta["RADIUS"]                           # R_sun
Rp = np.sqrt(depth_ppm / 1e6) * R_star * 109.1       # R_earth
print(f"depth = {depth_ppm:.0f} ppm, noise per point = {noise_ppm:.0f} ppm")
print(f"planet radius = {Rp:.1f} R_earth")

ax = folded.scatter(alpha=0.3)
folded.bin(time_bin_size=10 / (60 * 24)).plot(ax=ax, color="C3", lw=2)
ax.set_xlim(-0.2, 0.2)
plt.show()
```

Output:

```text
depth = 10830 ppm, noise per point = 613 ppm
planet radius = 15.3 R_earth
```

We only measure the **core** of the transit (the central half of the duration) to stay away from the sloped edges, where the planet enters and leaves. The radius comes from the rule in lesson B2, the same `planet_radius` function from [lesson P1](p1-python-basics.md).

### Comparing with PlanetHunter and ExoFOP

| Source | Period (d) | Depth (ppm) | Radius (R⊕) |
|---|---|---|---|
| You, with BLS | 0.94130 | 10,830 | 15.3 |
| PlanetHunter, sector 69 (TLS) | 0.941592 | 10,583 | 15.1 |
| ExoFOP, TOI-185.01 (several sectors) | 0.941453 | 11,445 | 15.3 |

The numbers agree within a few percent. The differences come from the method (a box in BLS, a realistic transit model in TLS), from how many sectors went in and from where the "bottom" is measured. Dedicated studies that model limb darkening (lesson M2) find a slightly smaller radius, about 1.2 Jupiter radii. The formula $\delta \approx (R_p/R_\star)^2$ is an approximation: the center of the star is brighter than its edge, so the core of the transit is a little deeper than $(R_p/R_\star)^2$.

!!! tip "In the tool"
    PlanetHunter does the same steps with other tools: cleaning in `src/planethunter/preprocess/clean.py`, detrending with the biweight filter from the wotan library (a 1-day window, instead of Lightkurve's filter) and a TLS search in `src/planethunter/search/tls.py`, instead of BLS. For WASP-18 b in sector 69 it recorded SDE 36.1, SNR 473.8 and 21 transits with data. The dossier shows the same "folded transit" you just drew.

!!! question "Something to think about"
    Repeat sections 2 to 5 with `search.download_all().stitch()`, which downloads and joins all the sectors in the search. With transits spread over years, what happens to the precision of the period? And to the BLS computing time? Hint: with years of data, the grid of 20,000 periods between 0.5 and 10 days becomes too coarse and misses the peak; use a fine grid around the known value, such as `np.linspace(0.94, 0.943, 20000)`.

## 6. Reading the Parquet file saved by PlanetHunter

When PlanetHunter downloads a light curve, it converts it to **Parquet**, a compact and fast table format. The path follows a pattern:

```text
data/parquet/sector=0069/author=SPOC/tic_0000000100100827.parquet
```

The sector has 4 digits and the TIC has 16, padded with zeros. To get this file, run `uv run planethunter ingest target 100100827 --sectors 69` in the PlanetHunter folder (see the [lab](../lab/using-planethunter.md)).

```python
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(r"C:\Users\you\planethunter")        # change to your folder
path = ROOT / "data" / "parquet" / "sector=0069" / "author=SPOC" / f"tic_{100100827:016d}.parquet"

table = pq.read_table(path)
df = table.to_pandas()
print(df.dtypes)
print(len(df))                                    # 18098 rows

meta = json.loads(table.schema.metadata[b"planethunter"])
print(meta["sector"], meta["camera"], meta["procver"])
print(meta["star"]["radius_rsun"], meta["star"]["tmag"])
```

The columns:

| Column | Contents | Type |
|---|---|---|
| `time` | Time in BTJD | float64 |
| `flux`, `flux_err` | Corrected brightness (PDCSAP) and error, in e⁻/s | float32 |
| `sap_flux` | Brightness without SPOC's correction | float32 |
| `quality` | Problem flags (0 = all good) | int32 |
| `cadenceno` | Measurement number | int64 |
| `mom_centr1`, `mom_centr2` | Position of the light on the detector, in pixels | float32 |

The **metadata** live in the file header, as JSON text under the key `b"planethunter"`: sector, camera, processing version (`procver`), checksum of the original file and the star's parameters. The `b` before the quotes means bytes instead of text, which the format requires.

The file keeps **all** the measurements, including the bad ones. Filter them and turn the result into a LightCurve:

```python
from astropy.time import Time

good = df[(df["quality"] == 0) & np.isfinite(df["flux"])]
print(len(good))                                  # 14665, same as the download
lc_ph = lk.LightCurve(
    time=Time(good["time"].to_numpy(), format="btjd", scale="tdb"),
    flux=good["flux"].to_numpy(),
    flux_err=good["flux_err"].to_numpy(),
).normalize()
```

From here on, `lc_ph` accepts `flatten`, `fold` and `to_periodogram` as before.

## 7. Querying the DuckDB database

PlanetHunter stores its results in `data/planethunter.duckdb`, a database in a single file. You ask it questions in **SQL**, the standard language of databases. To get WASP-18 b into your database, run `uv run planethunter run-target 100100827 --sectors 69` in the PlanetHunter folder and then `uv run planethunter vet <run_id>`, with the `run_id` the first command prints. The main tables:

| Table | One row per | Useful columns |
|---|---|---|
| `signals` | signal found in the search | `signal_id`, `run_id`, `tic_id`, `period_days`, `depth_ppm`, `sde`, `snr`, `n_transits` |
| `crossmatch` | signal compared with the catalogs | `match_class`, `matched_name`, `host_known` |
| `vetting` | signal tested | `score`, `verdict`, `vetoed_by`, `failed`, `p_planet` |
| `candidates` | candidate in the queue | `severity`, `review_status` |

```python
import duckdb

con = duckdb.connect(str(ROOT / "data" / "planethunter.duckdb"), read_only=True)

print(con.sql("""
    SELECT signal_id, run_id, period_days, depth_ppm, sde, snr, n_transits
    FROM signals
    WHERE tic_id = 100100827
    ORDER BY signal_id
""").df())

print(con.sql("""
    SELECT s.signal_id, s.period_days, c.match_class, c.matched_name,
           v.verdict, v.score, v.failed
    FROM signals s
    JOIN crossmatch c USING (signal_id)
    LEFT JOIN vetting v USING (signal_id)
    WHERE s.tic_id = 100100827
""").df())

print(con.sql("""
    SELECT match_class, count(*) AS n
    FROM crossmatch GROUP BY match_class ORDER BY n DESC
""").df())
con.close()
```

Read the SQL as a sentence: "select (`SELECT`) these columns from the table (`FROM`) where (`WHERE`) the condition holds, in order of (`ORDER BY`)". `JOIN ... USING (signal_id)` joins two tables on the rows that have the same `signal_id`. `.df()` returns a pandas DataFrame.

In the project's database, on 2026-10-09, the slice of 2,164 stars from sector 69 (run `20261009T204130Z-single-s69`) recorded WASP-18 b as signal 2020: `KNOWN_PLANET`, matched to TOI-185.01. The basic vetting gave `FAIL`, score 0.2, with failures in `secondary` and `consistency`. Vetting is not perfect: it approves about 81 % of the confirmed planets in sector 69. This does not cause a false alert, because a `KNOWN_PLANET` never becomes a candidate.

!!! warning "Database in use"
    Always open it with `read_only=True` and close it with `con.close()`. If a PlanetHunter command is running, DuckDB may refuse the connection with a "lock" error. Wait for the command to finish.

## Exercises

!!! example "Exercise 1. Odd and even"
    An eclipsing binary with twice the period shows alternating eclipses of different depths (lesson B4). Measure the depth of the odd and even transits of WASP-18 b.

    ??? success "Show answer"
        ```python
        t = np.asarray(flat.time.value, dtype=float)
        f = np.asarray(flat.flux.value, dtype=float)
        n = np.round((t - T0) / P).astype(int)          # number of each transit
        core = np.abs(t - (T0 + n * P)) < 0.25 * D
        odd = (1 - np.median(f[core & (n % 2 == 1)])) * 1e6
        even = (1 - np.median(f[core & (n % 2 == 0)])) * 1e6
        print(f"odd {odd:.0f} ppm, even {even:.0f} ppm")
        ```
        Result: about 10,770 ppm for the odd transits and 10,880 for the even ones, a 1 % difference. For a binary with a doubled period, the difference is usually large. This is what the vetting's `odd_even` test measures, with error bars.

!!! example "Exercise 2. Looking at phase 0.5"
    WASP-18 b is so hot that TESS sees the planet's own light disappear when it passes behind the star. Measure the brightness at phase 0.5 (halfway between transits). Compare with PlanetHunter's rule: the `secondary` test only vetoes if the secondary dip is at least 10 % of the main one.

    ??? success "Show answer"
        ```python
        sec = np.abs(np.abs(phase) - 0.5 * P) < 0.25 * D
        sec_depth = (level - np.median(flux[sec])) * 1e6
        print(f"phase 0.5: {sec_depth:.0f} ppm = {100 * sec_depth / depth_ppm:.1f} % of the main one")
        ```
        It comes to about 310 ppm, close to 3 % of the main dip. The project's vetting calibration (sector 69) records about 340 ppm for this occultation. Part of the value may come from the brightness variation along the orbit, which the 30-hour window does not fully remove. Since 3 % is below 10 %, the rule does not veto. The test still records a soft fail, which lowers the score: that is why signal 2020 shows `secondary` in the `failed` column. Before this rule, the system vetoed WASP-18 b as a binary (guide, section 5).

!!! example "Exercise 3. Counting candidates"
    Write an SQL query that counts the candidates by severity and by review status.

    ??? success "Show answer"
        ```python
        con = duckdb.connect(str(ROOT / "data" / "planethunter.duckdb"), read_only=True)
        print(con.sql("""
            SELECT severity, review_status, count(*) AS n
            FROM candidates
            GROUP BY severity, review_status
            ORDER BY severity
        """).df())
        con.close()
        ```
        `GROUP BY` with two columns creates a group for each combination. In the project's database, on 2026-10-09: 13 P1 pending, 49 P2 pending, 2 P2 rejected and 1 P2 in `follow_up`. Your database will have different numbers. P1 and P2 are not planets: they are signals waiting for human review.

## Lesson checklist

- [ ] I searched for and downloaded the sector 69 light curve of WASP-18
- [ ] I cleaned the curve, cutting only high points
- [ ] I found the period with BLS in two passes, with the transits masked
- [ ] I folded the curve, measured the depth and estimated the radius
- [ ] I compared my numbers with PlanetHunter and ExoFOP
- [ ] I read a PlanetHunter Parquet file and the metadata under the `b"planethunter"` key
- [ ] I queried `signals`, `crossmatch`, `vetting` and `candidates` with SQL
- [ ] I solved the three exercises

## Going further

- Lightkurve tutorials ([lightkurve.github.io](https://lightkurve.github.io/lightkurve/tutorials/index.html)), especially "Identifying transiting exoplanet signals". The path of this lesson follows the same route, with more detail on each function.
- Astropy documentation on Box Least Squares ([docs.astropy.org](https://docs.astropy.org/en/stable/timeseries/bls.html)). Lightkurve's BLS calls this implementation under the hood.
- WASP-18 b's page on the NASA Exoplanet Archive ([exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu/overview/WASP-18%20b)). Gathers the published parameters to compare with your measurement.
