---
name: exoplanet-crossmatch
description: How to check whether an exoplanet candidate is already known. TAP queries to the NASA Exoplanet Archive (ps, pscomppars, toi), ExoFOP CSVs (TOI, CTOI), exoplanet.eu, EB catalogs, cone search with proper motion, period matching with aliases and NEW/KNOWN_* classes. Use for catalog mirrors and for the crossmatch engine.
---

# "Does it already exist?" crossmatch

## Mirrors (daily sync to Parquet)

NASA Exoplanet Archive via TAP (synchronous, CSV):

```python
import pandas as pd, urllib.parse as up

TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?format=csv&query="


def tap(q):
    return pd.read_csv(TAP + up.quote(q))


planets = tap(
    "select pl_name,hostname,tic_id,gaia_id,ra,dec,pl_orbper,pl_tranmid,"
    "pl_trandep,pl_trandur,pl_rade,disc_facility,disc_year from pscomppars"
)
toi = tap(
    "select toi,tid,tfopwg_disp,ra,dec,pl_orbper,pl_tranmid,pl_trandep,"
    "pl_trandurh,pl_rade,st_tmag from toi"
)
```
With astroquery: `NasaExoplanetArchive.query_criteria(table="pscomppars", select=..., where=...)`. TOI columns: https://exoplanetarchive.ipac.caltech.edu/docs/API_toi_columns.html. `tid` = TIC ID. Dispositions: CP, KP, PC, APC, FP, FA.

ExoFOP-TESS:

```python
toi_x = pd.read_csv("https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv")
ctoi_x = pd.read_csv("https://exofop.ipac.caltech.edu/tess/download_ctoi.php?sort=ctoi&output=csv")
# columns: "TIC ID", "TOI"/"CTOI", "Period (days)", "Epoch (BJD)", "Depth (ppm)", "TFOPWG Disposition"
```

Others: exoplanet.eu (CSV export on the site), Open Exoplanet Catalogue (GitHub XML), TESS EB Catalog Prša+2022 (VizieR J/ApJS/258/16), Gaia DR3 `vari_eclipsing_binary` (VizieR I/358). SIMBAD only on demand.

Common schema: `source, name, host, tic_id:int64, gaia_id:int64, ra, dec, pmra, pmdec, epoch, period, t0, depth_ppm, duration_h, disposition, url`. Normalize `tic_id` to an integer without prefix. Record in `catalog_mirrors` with `synced_at, n_rows, checksum`.

## Match layers

1. Exact ID: `tic_id`, `gaia_id`, KIC/EPIC, TOI.
2. Position with proper motion:

```python
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

c0 = SkyCoord(
    ra * u.deg,
    dec * u.deg,
    pm_ra_cosdec=pmra * u.mas / u.yr,
    pm_dec=pmdec * u.mas / u.yr,
    obstime=Time(2016.0, format="jyear"),
    distance=1000 / plx * u.pc,
)
c_obs = c0.apply_space_motion(new_obstime=Time(btjd + 2457000, format="jd"))
sep = c_obs.separation(cat_coords).arcsec
match = sep < 21  # 1 TESS pixel
nearby = (sep >= 21) & (sep < 120)
```
Pre-filter in DuckDB by HEALPix (`astropy_healpix`, nside 4096 ≈ 51") comparing the pixel and its neighbors.

3. Period with aliases and phase:

```python
import numpy as np

ALIASES = np.array([1, 2, 0.5, 3, 1 / 3, 1.5, 2 / 3])


def period_match(p_c, t0_c, p_k, t0_k, tol=0.01):
    ratio = p_c / p_k
    k = ALIASES[np.argmin(np.abs(ratio / ALIASES - 1))]
    if abs(ratio / k - 1) > tol:
        return None
    phase = ((t0_c - t0_k) / p_k + 0.5) % 1 - 0.5
    return dict(alias=k, dphase=phase) if abs(phase) < 0.05 else None
```
Watch the T0 units: ExoFOP uses BJD, we use BTJD (BJD − 2457000).

4. Reinforcement: depth and duration within 3σ.


## Classes

| Class | Condition |
|---|---|
| `KNOWN_PLANET` | confirmed (Archive `pscomppars`, CP/KP in any catalog: exoplanet.eu, TOI, KOI, K2) on the host + compatible signal |
| `KNOWN_TOI` | ExoFOP TOI (PC/APC) on the host + compatible signal |
| `KNOWN_CTOI` | ExoFOP CTOI on the host + compatible signal |
| `KNOWN_PUBLISHED` | published/cataloged candidate outside TOI/CTOI (KOI/K2 candidates, exoplanet.eu non-confirmed, DIAmante, DTARPS-S, LEO-Vetter, ExoMiner++) |
| `KNOWN_FP` | FP/FA/EB disposition, or an EB catalog (Prša+2022, Kostov+2025) with any alias in tolerance |
| `NEARBY_KNOWN` | known object at 21"–2' with a compatible signal |
| `NEW` | no compatible signal in any mirror, every mirror fresh for its policy |
| `UNVERIFIED` | NEW but some mirror missing/stale: alerting forbidden |

Match by ID or position without a compatible signal in a system with a known planet = possible additional planet: class `NEW` with `host_known=True` (great niche).

## Literature (outside the critical path)

ADS: `GET https://api.adsabs.harvard.edu/v1/search/query?q=full:"TIC 123456789"&fl=bibcode,title,year` with a token. arXiv: `http://export.arxiv.org/api/query?search_query=all:"TIC 123456789"`.

## Mandatory tests

- All confirmed planets in the benchmark sector → `KNOWN_PLANET`.
- Aliases: P=2.0 vs 4.0, 1.0 vs 3.0, 3.0 vs 2.0 match; 2.0 vs 2.05 does not.
- A mirror missing or older than its freshness policy (48 h for ExoFOP/Archive) blocks `NEW` classification and alerts.
- A host that gets a TOI after the batch crossmatch is not alerted (send-time re-check).

## State in the code (v2, 2026-10-10 audit)

Modules: `crossmatch/core.py` (per-signal classification), `crossmatch/batch.py` (star selection + DataFrame classification, shared with the alert gate), `crossmatch/runlevel.py` (run-level flags), `catalogs/mirrors.py` (sync, manifest, freshness), `pipeline.run_crossmatch`, `alerts/notify.py` (send-time gate). Thresholds: `crossmatch:` in `config/thresholds.yaml`.

- **Mirrors (12 sources):** Archive `pscomppars`, ExoFOP TOI/CTOI, exoplanet.eu (all statuses mapped; the CSV export currently contains only Confirmed), Kepler KOI `cumulative`, K2 `k2pandc` (default set), VizieR: TESS EBs Prša+2022, TESS Ten Thousand EBs Kostov+2025 (table3 + table4), DIAmante Montalto+2020, DTARPS-S Melton+2024 (table1 + table4), LEO-Vetter Kunimoto+2025 (table3), ExoMiner++ Valizadegan+2025 (table13 PC + table16). Each sync writes `<stamp>.parquet` + `<stamp>.json` (n_rows, sha256, version, url); contract check (expected raw columns, no drop > 10 %). CTOI epochs in BJD−2400000 are converted; anything outside −1e4 < BTJD < 1e4 is nulled.
- **Freshness per source:** live 48 h (TOI, CTOI, Archive), 168 h (exoplanet.eu, K2), 720 h (KOI), static VizieR catalogs never expire but must match the code's `MirrorSpec.version`. `mirrors status` exits 1 if any source is missing/stale/wrong version. `run_crossmatch` upserts the manifest into `catalog_mirrors` (source, file, synced_at, n_rows, sha256, version, max_age_hours); a crossmatch row links to its files through `checked_at` (UTC) − `mirror_ages_json[source]`.
- **Star:** exact integer TIC, else the minimum distance between the catalog position and the target's proper-motion track from J2000 to the observation epoch (catalog epochs are mixed). Host < 21", neighbors < 2'.
- **Period:** tolerance max(1 %, 3σ_P/P of the candidate) capped at 3 %; beyond 1 % the phase is mandatory. Alias 1 within 1 % = known at any phase (drift). Alias ≠ 1 needs a consistent phase (else "resonance" note, NEW). EB/FP: any alias, any phase (secondary/eccentric) within 1 %. Missing σ_P = 1e-4·P. Phase tolerance ≥ 0.5 → `phase_checked=False`.
- **Integer harmonics (host only):** n or 1/n up to 50 (EB/FP also n/2, with secondaries), phase mandatory, chance probability (period coincidence × phase coverage) < 0.05. Catches TOI-4981.01 (×4 of a 0.21 d TOI), TOI-5678, TOI-4666.
- **Period-less TOIs/CTOIs/candidates:** match if the candidate ephemeris predicts the known epoch; otherwise NEW with the notes token `periodless_known_on_host`.
- **Transit by transit:** window max(0.5 D, 1 h) + 3σ_prop; skip objects with 3σ_prop > min(0.25 d, 0.1 P); phase 0.5 never for a period that is a confirmed planet in any catalog; all objects explaining each transit are collected; same-period objects (one planet in several catalogs) count once; chance = binomial P(X ≥ k | n, f_obs) with f_obs from the largest observed residual (floor 15 min); known if k/n ≥ 0.5 and chance < 1e-2. Measured chance-match rate 0.3–1.3 % (old matcher 36 %). Marginal cases (0.01 ≤ chance < 0.1) stay NEW with the token `partial_known_transit_coincidence` (GJ 143 signal 2129 in sector 69).
- **Precedence:** all evidence on the host is collected first, then confirmed planet > TFOPWG FP/FA > TOI > CTOI > published candidate > EB catalog.
- **`host_eb`:** host has an EB-catalog row whose period does not match (alias 1) a planet/candidate row of the same host (WASP-173 A b fix). Severity caps at P2.
- **Run-level flags (`runlevel.py`):** `epoch_spike_frac` (fraction of transits in common-epoch spikes; histogram of distinct targets per 0.25 d bin from few-transit signals, two offset grids, leave-one-target-out, spike ≥ max(5×median, median + 5√median, 5); NULL with < 100 targets) and `shared_signal_{tic,sep_arcsec,role}` (same P (1, 2, 1/2) and T0 on another target within 2'; role duplicate ≤ 2", else source = larger eclipsed flux depth×10^(−0.4 Tmag) with required depth ≤ 1, victim otherwise, both victims if comparable flux > 1 px apart). Severity: spike frac ≥ `epoch_spike_max_frac` (0.5) or duplicate/victim → no alert; source → P2.
- **Alert gate:** `send_alerts` re-classifies every P0/P1 against freshly loaded mirrors right before sending (and in dry-run), refuses if any mirror is stale or the class is no longer NEW, and updates the crossmatch row; `checked_at` is UTC.
