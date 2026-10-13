---
name: tess-data-access
description: Recipes for downloading and storing TESS light curves, TPFs and stellar parameters (MAST, lightkurve, TESScut, HLSPs, TIC, Gaia). Use when you need to obtain TESS photometry, choose an author (SPOC/QLP/TESS-SPOC), extract from FFIs, query TIC/Gaia or convert to Parquet.
---

# TESS data access

## Choosing the source

| I need | Use |
|---|---|
| Best precision, bright targets | `author="SPOC"`, `exptime=120` (or 20) |
| Faint stars in FFIs, ~160k/sector | `author="TESS-SPOC"` (HLSP) |
| Comparison / Tmag ≤ 13.5 | `author="QLP"` |
| Any star, our own extraction | `search_tesscut` + manual aperture, or `eleanor` |
| Centroid / difference image | `search_targetpixelfile` |

## Light curve

```python
import lightkurve as lk

sr = lk.search_lightcurve("TIC 261136679", mission="TESS", author="SPOC", exptime=120)
lcs = sr.download_all(flux_column="pdcsap_flux", quality_bitmask="default")
lc = lcs.stitch().remove_nans()  # stitch normalizes per sector
# Do NOT use symmetric remove_outliers: it clips transits. Upward only:
lc = lc.remove_outliers(sigma_upper=4, sigma_lower=1e9)
t, f, e = lc.time.value, lc.flux.value.astype("float32"), lc.flux_err.value.astype("float32")
# time in BTJD (BJD - 2457000); lc.sector, lc.meta["AUTHOR"], lc.meta["PROCVER"]
```

## FFI via TESScut

```python
sr = lk.search_tesscut("TIC 123456789", sector=70)
tpf = sr.download(cutout_size=11)
aper = tpf.create_threshold_mask(threshold=3)
lc = tpf.to_lightcurve(aperture_mask=aper)
bkg = tpf.to_lightcurve(aperture_mask=~aper & (tpf.flux[0].value > 0))
```

## TPF for centroid

```python
tpf = lk.search_targetpixelfile("TIC 261136679", sector=1, author="SPOC").download()
# tpf.wcs, tpf.pipeline_mask, tpf.flux (cadences, y, x)
```

## Stellar parameters

```python
from astroquery.mast import Catalogs

tic = Catalogs.query_object("TIC 261136679", catalog="TIC")
# columns: ra, dec, pmRA, pmDEC, Tmag, Teff, rad, mass, rho, contratio, GAIA
```

Gaia DR3 neighbors (for blends):

```python
from astroquery.gaia import Gaia
from astropy.coordinates import SkyCoord
import astropy.units as u

job = Gaia.cone_search_async(SkyCoord(ra, dec, unit="deg"), radius=1 * u.arcmin)
nb = job.get_results()  # source_id, ra, dec, pmra, pmdec, phot_g_mean_mag, parallax
```

## Bulk per sector

MAST publishes `tesscurl_sector_<N>_lc.sh` scripts at https://archive.stsci.edu/tess/bulk_downloads.html. Parse the URLs, download with ≤ 8 connections, retry with backoff, checksum.

## Parquet

Schema: `time float64 (BTJD), flux float32, flux_err float32, quality int32, cadenceno int64`. Partition `data/parquet/sector=N/author=X/tic_id.parquet`. Metadata in the footer: author, procver, sector, camera, ccd, sha256 of the FITS. 1 SPOC 2-min sector ≈ 6 GB in Parquet versus ~40 GB in FITS.

## Pitfalls

- `stitch()` normalizes each sector by its median; do not use it before measuring absolute depth if you need raw flux.
- Momentum dumps are in `quality` bit 32 (or via `lk.utils.TessQualityFlags`).
- TESScut has a cutout size limit and a rate limit; caching is mandatory.
- TIC `contratio` is the contamination ratio in the SPOC aperture; it does not apply to your own aperture.

## State in the code (v1)

- Bulk per sector: `ingest/mast.py::ingest_sector` reads `tesscurl_sector_N_lc.sh` (sector 107 = most recent as of 2026-10-09, 12 998 light curves). ~2000 stars in 3.7 min with 8 simultaneous downloads; FITS deleted after conversion.
- Stellar parameters come from the SPOC header (TESSMAG, TEFF, LOGG, RADIUS, RA_OBJ, PMRA, CROWDSAP); mass estimated from logg and radius. No TIC query at ingest.
- Parquet also stores MOM_CENTR1/2 (per-cadence centroid) for the offline centroid test.
- PDCSAP already corrects for crowding: do not apply CROWDSAP again to the depth.
