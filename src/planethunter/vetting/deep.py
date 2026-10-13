"""Deep vetting per candidate (network, cached): tests 9, 10 and 13 of docs/PLAN.md §6.

9  TPF difference image: where on the detector is the transit source? The difference-image
   centroid is compared with the CATALOG position (TIC, propagated with proper motion to the
   observation epoch), 3 sigma and > 1 px (Bryson et al. 2013).
10 Gaia DR3 neighbors: could any nearby star produce the observed dip? Required depth per
   neighbor with the triceratops formula (Gaussian PSF integrated over the real aperture,
   TESS magnitudes; Giacalone et al. 2021).
13 FPP (triceratops) runs in an isolated environment: it needs numpy 1.26 / scipy 1.13 and
   would break the main environment (TLS 2.0 with numpy 2.x).

The functions `difference_image_test`, `neighbors_test`, `sector_presence`, `simbad_test`,
`gaia_eb_test` and `fpp_test` are pure (arrays and DataFrames) and testable offline.
`fetch_*` touch the network and write a cache under <data>/cache/.

Units: time BTJD, period/duration days, depth ppm, separations arcsec, positions degrees,
proper motions mas/yr (pmra = mu_alpha * cos(dec)).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

from planethunter.vetting.basic import TestResult, epoch_index, phase_days

PIXEL_ARCSEC = 21.0
GAIA_VIZIER = "I/355/gaiadr3"
TIC_EPOCH_JYEAR = 2000.0  # TIC v8 positions are given at epoch J2000
GAIA_DR3_EPOCH_JYEAR = 2016.0
BTJD_TO_JD = 2457000.0


# ---------------------------------------------------------------- astrometry helpers


def btjd_to_jyear(btjd: float) -> float:
    """Julian epoch (years) of a BTJD time."""
    return 2000.0 + (btjd + BTJD_TO_JD - 2451545.0) / 365.25


def propagate_position(
    ra_deg: float,
    dec_deg: float,
    pmra_mas_yr: float | None,
    pmdec_mas_yr: float | None,
    from_jyear: float,
    to_jyear: float,
) -> tuple[float, float]:
    """Linear proper-motion propagation (degrees). Missing proper motion = no motion.

    pmra is mu_alpha* = mu_alpha cos(dec) (TIC and Gaia convention). Linear propagation is
    accurate to < 1 mas over decades except for the nearest stars, far below a TESS pixel.
    """
    pmra = pmra_mas_yr if pmra_mas_yr is not None and np.isfinite(pmra_mas_yr) else 0.0
    pmdec = pmdec_mas_yr if pmdec_mas_yr is not None and np.isfinite(pmdec_mas_yr) else 0.0
    dt = to_jyear - from_jyear
    cosd = math.cos(math.radians(dec_deg))
    dra = pmra * dt / 3.6e6 / max(cosd, 1e-6)
    ddec = pmdec * dt / 3.6e6
    return float((ra_deg + dra) % 360.0), float(dec_deg + ddec)


def gaia_g_to_tmag(g: np.ndarray, bp_rp: np.ndarray | None = None) -> np.ndarray:
    """TESS magnitude from Gaia G (Stassun et al. 2019, TIC v8, eq. 1; scatter 0.006 mag).

    T = G - 0.00522555 c^3 + 0.0891337 c^2 - 0.633923 c + 0.0324473, c = BP - RP, used for
    -0.2 < c < 3.0 (clipped outside). Without a color: T = G - 0.430 (same paper; 0.6 mag).
    """
    g = np.asarray(g, dtype=float)
    if bp_rp is None:
        return g - 0.430
    c = np.asarray(bp_rp, dtype=float)
    cc = np.clip(c, -0.2, 3.0)
    t = g - 0.00522555 * cc**3 + 0.0891337 * cc**2 - 0.633923 * cc + 0.0324473
    return np.where(np.isfinite(c), t, g - 0.430)


def psf_fraction_in_aperture(
    x: float, y: float, aperture: np.ndarray, sigma_px: float = 0.75
) -> float:
    """Fraction of a circular Gaussian PSF centred at (x, y) that falls in `aperture`.

    `aperture` is a bool (ny, nx) mask; pixel (row j, column i) spans i +- 0.5, j +- 0.5.
    Same closed-form pixel integral as triceratops `calc_depths` (sigma = 0.75 px).
    """
    ys, xs = np.nonzero(aperture)
    if len(xs) == 0:
        return 0.0
    fx = ndtr((xs + 0.5 - x) / sigma_px) - ndtr((xs - 0.5 - x) / sigma_px)
    fy = ndtr((ys + 0.5 - y) / sigma_px) - ndtr((ys - 0.5 - y) / sigma_px)
    return float(np.sum(fx * fy))


def _gaia_id(x) -> str:
    """Gaia source_id as an exact int64 string (never via float)."""
    if isinstance(x, str):
        return x
    try:
        return str(np.int64(x))
    except (TypeError, ValueError, OverflowError):
        return str(x)


# ---------------------------------------------------------------- 9: difference image


@dataclass
class PixelData:
    """TPF cutout needed by the test. flux: (n_cadences, ny, nx) in e-/s."""

    time: np.ndarray
    flux: np.ndarray
    quality_ok: np.ndarray
    aperture: np.ndarray  # bool (ny, nx), pipeline mask
    target_xy: tuple[float, float]  # target column, row (pixels, origin 0 in the cutout)
    sector: int
    origin: tuple[int, int] = (0, 0)  # column, row of the cutout corner on the CCD
    wcs: object | None = field(default=None, repr=False)  # astropy WCS of the cutout

    def aperture_pixels(self) -> list[list[int]]:
        """Aperture pixels in absolute CCD coordinates [column, row] (triceratops)."""
        ys, xs = np.nonzero(self.aperture)
        return [
            [int(self.origin[0] + x), int(self.origin[1] + y)] for y, x in zip(ys, xs, strict=True)
        ]

    def epoch_jyear(self) -> float:
        return btjd_to_jyear(float(np.nanmedian(self.time)))


def _centroid(img: np.ndarray, frac: float = 0.3) -> tuple[float, float] | None:
    """Weighted centroid of the pixels above `frac` of the maximum (positive values)."""
    if not np.isfinite(img).any():
        return None
    peak = np.nanmax(img)
    if not np.isfinite(peak) or peak <= 0:
        return None
    w = np.where(np.isfinite(img) & (img >= frac * peak), img, 0.0)
    if w.sum() <= 0:
        return None
    yy, xx = np.indices(img.shape)
    return float((w * xx).sum() / w.sum()), float((w * yy).sum() / w.sum())


def difference_image_test(
    pix: PixelData,
    period: float,
    t0: float,
    duration_days: float,
    *,
    max_offset_px: float = 1.0,
    nsigma: float = 3.0,
) -> tuple[TestResult, dict]:
    """Difference-image (out - in) centroid against the catalog position of the target.

    Transit on the target: the difference has the target's PSF and its centroid falls on the
    TIC position. Transit on a neighbor: it shifts. Bryson et al. 2013 decide against the
    catalog position (3 sigma); comparing with the out-of-transit centroid (as before) failed
    10 of 20 sector-107 candidates whose difference centroid was within 1 px of the TIC
    position. Uncertainty = scatter of the per-transit centroids / sqrt(n). Fails only if the
    catalog offset is > nsigma AND > max_offset_px. With < 3 transits there is no error
    estimate: an offset > max_offset_px is indeterminate (Kostov et al. 2019).
    """
    name = "tpf_difference_image"
    ok = pix.quality_ok & np.isfinite(pix.flux).all(axis=(1, 2))
    t, cube = pix.time[ok], pix.flux[ok]
    ph = phase_days(t, period, t0)
    ep = epoch_index(t, period, t0)
    inn = np.abs(ph) < 0.4 * duration_days
    out = (np.abs(ph) > 1.0 * duration_days) & (np.abs(ph) < 3.0 * duration_days)
    if inn.sum() < 3 or out.sum() < 10:
        return TestResult(name, None, max_offset_px, None, note="too few points in TPF"), {}
    oot = cube[out].mean(axis=0)
    diff = oot - cube[inn].mean(axis=0)
    c_diff, c_oot = _centroid(diff), _centroid(oot)
    if c_diff is None or c_oot is None:
        return TestResult(name, None, max_offset_px, None, note="no signal in difference image"), {}
    per = []
    for e in np.unique(ep[inn]):
        i = inn & (ep == e)
        o = out & (ep == e)
        if i.sum() >= 3 and o.sum() >= 5:
            c = _centroid(cube[o].mean(axis=0) - cube[i].mean(axis=0))
            if c is not None:
                per.append(c)
    off_oot = math.hypot(c_diff[0] - c_oot[0], c_diff[1] - c_oot[1])
    off_cat = math.hypot(c_diff[0] - pix.target_xy[0], c_diff[1] - pix.target_xy[1])
    err = (
        float(np.hypot(*np.std(np.array(per), axis=0, ddof=1)) / math.sqrt(len(per)))
        if len(per) >= 3
        else float("nan")
    )
    has_err = bool(np.isfinite(err) and err > 0)
    significant = has_err and off_cat / err > nsigma
    if has_err:
        passed: bool | None = not (significant and off_cat > max_offset_px)
    else:
        passed = True if off_cat <= max_offset_px else None
    info = {
        "diff": diff,
        "oot": oot,
        "c_diff": c_diff,
        "c_oot": c_oot,
        "aperture": pix.aperture,
        "target_xy": pix.target_xy,
    }
    note = (
        f"sector {pix.sector}: difference centroid {off_cat:.2f} px "
        f'({off_cat * PIXEL_ARCSEC:.0f}") from TIC position (proper motion applied), '
        f"{off_oot:.2f} px from out-of-transit centroid; error {err:.2f} px ({len(per)} transits)"
    )
    if passed is None:
        note += "; offset with < 3 transits: indeterminate"
    return (
        TestResult(
            name,
            off_cat,
            max_offset_px,
            passed,
            note=note,
            extra={
                "sector": int(pix.sector),
                "c_diff": [float(c_diff[0]), float(c_diff[1])],
                "target_xy": [float(pix.target_xy[0]), float(pix.target_xy[1])],
                "err_px": err if has_err else None,
                "offset_significant": bool(significant and off_cat > max_offset_px),
            },
        ),
        info,
    )


# ---------------------------------------------------------------- 10: Gaia neighbors


def neighbor_pixels(nb: pd.DataFrame, pix: PixelData) -> pd.DataFrame:
    """Add x_px, y_px (cutout pixels) to Gaia neighbors, propagated from 2016.0 to the TPF epoch."""
    if pix.wcs is None or nb.empty:
        return nb
    to = pix.epoch_jyear()
    pmra = nb["pmRA"] if "pmRA" in nb else pd.Series(np.nan, index=nb.index)
    pmde = nb["pmDE"] if "pmDE" in nb else pd.Series(np.nan, index=nb.index)
    pos = [
        propagate_position(r, d, pa, pd_, GAIA_DR3_EPOCH_JYEAR, to)
        for r, d, pa, pd_ in zip(nb["RA_ICRS"], nb["DE_ICRS"], pmra, pmde, strict=True)
    ]
    ra = np.array([p[0] for p in pos])
    dec = np.array([p[1] for p in pos])
    x, y = pix.wcs.all_world2pix(ra, dec, 0)
    return nb.assign(x_px=np.asarray(x, float), y_px=np.asarray(y, float))


def _circular_aperture(radius_px: float = 1.5, half: int = 6) -> tuple[np.ndarray, tuple]:
    yy, xx = np.indices((2 * half + 1, 2 * half + 1))
    return np.hypot(xx - half, yy - half) <= radius_px, (float(half), float(half))


def neighbors_test(
    neighbors: pd.DataFrame,
    target_tmag: float,
    depth_ppm: float,
    *,
    exclusion_radius_arcsec: float,
    search_radius_arcsec: float = 2.5 * PIXEL_ARCSEC,
    aperture: np.ndarray | None = None,
    target_xy: tuple[float, float] | None = None,
    psf_sigma_px: float = 0.75,
    diff_xy: tuple[float, float] | None = None,
    diff_offset_significant: bool = False,
    diff_radius_px: float = 1.0,
) -> TestResult:
    """Gaia neighbors that could be the source and that the centroid does not rule out.

    `neighbors` (target excluded): sep_arcsec and Tmag (or Gmag [+ BP-RP], converted with
    Stassun et al. 2019); optional x_px, y_px in the cutout. Required intrinsic depth on a
    neighbor (triceratops `calc_depths`, Giacalone et al. 2021) for a dilution-corrected
    (PDCSAP) depth delta: delta * F_target,ap / F_neighbor,ap, with F_ap = 10^(-0.4 T) x the
    fraction of a Gaussian PSF (sigma 0.75 px) inside the aperture. > 1 is impossible. Without
    a TPF aperture a 1.5 px circular aperture centred on the target is assumed.

    Outcomes: passed=True (no neighbor can produce the dip, or none is unresolved);
    passed=None with value = number of plausible unresolved neighbors ("needs high-resolution
    imaging"); passed=False if the difference image shows a significant offset and a neighbor
    able to produce the dip lies within `diff_radius_px` of the difference centroid (audit G6).
    Errors (no Gaia data) are reported by the caller with value=None.
    """
    name = "gaia_neighbors"
    nb = neighbors[neighbors["sep_arcsec"] < search_radius_arcsec].copy()
    if nb.empty:
        return TestResult(
            name, 0, 0, True, note=f'no Gaia neighbors within {search_radius_arcsec:.0f}"'
        )
    if "Tmag" not in nb:
        nb["Tmag"] = gaia_g_to_tmag(nb["Gmag"], nb.get("BP-RP"))
    approx = aperture is None or target_xy is None or not {"x_px", "y_px"} <= set(nb.columns)
    if approx:
        aperture, target_xy = _circular_aperture()
        nb["x_px"] = target_xy[0] + nb["sep_arcsec"] / PIXEL_ARCSEC
        nb["y_px"] = target_xy[1]
    frac_t = psf_fraction_in_aperture(target_xy[0], target_xy[1], aperture, psf_sigma_px)
    nb["frac_ap"] = [
        psf_fraction_in_aperture(x, y, aperture, psf_sigma_px)
        for x, y in zip(nb["x_px"], nb["y_px"], strict=True)
    ]
    f_t = frac_t * 10 ** (-0.4 * target_tmag)
    f_nb = nb["frac_ap"] * 10 ** (-0.4 * nb["Tmag"])
    with np.errstate(divide="ignore"):
        nb["depth_needed"] = np.where(f_nb > 0, depth_ppm * 1e-6 * f_t / f_nb, np.inf)
    possible = nb[nb["depth_needed"] <= 1.0]
    unresolved = possible[possible["sep_arcsec"] < exclusion_radius_arcsec]
    note = (
        f'{len(nb)} neighbors within {search_radius_arcsec:.0f}"; {len(possible)} could produce '
        f"the dip; {len(unresolved)} inside the centroid exclusion radius "
        f'({exclusion_radius_arcsec:.0f}")' + ("; aperture approximated (no TPF)" if approx else "")
    )
    extra: dict = {"n_possible": int(len(possible)), "n_unresolved": int(len(unresolved))}
    # G6: neighbors at the difference-image centroid.
    if diff_xy is not None and not approx and len(possible):
        d = np.hypot(possible["x_px"] - diff_xy[0], possible["y_px"] - diff_xy[1])
        at_diff = possible[d <= diff_radius_px].assign(d_px=d[d <= diff_radius_px])
        if len(at_diff):
            ids = [
                f'{_gaia_id(r.get("Source", "?"))} (T {r["Tmag"]:.1f}, {r["sep_arcsec"]:.0f}", '
                f"needs {r['depth_needed']:.1%})"
                for _, r in at_diff.sort_values("d_px").head(3).iterrows()
            ]
            extra["at_difference_centroid"] = [_gaia_id(s) for s in at_diff.get("Source", [])]
            note += "; near the difference centroid: " + ", ".join(ids)
            if diff_offset_significant:
                return TestResult(
                    name,
                    float(len(at_diff)),
                    0,
                    False,
                    note=note + " — likely transit source",
                    extra=extra,
                )
    if len(unresolved):
        closest = unresolved.sort_values("sep_arcsec").iloc[0]
        note += (
            f'; closest at {closest["sep_arcsec"]:.1f}" with T {closest["Tmag"]:.1f} '
            f"(would need {closest['depth_needed']:.0%} depth)"
        )
        return TestResult(
            name,
            float(len(unresolved)),
            0,
            None,
            note=note + "; plausible neighbor: needs high-resolution imaging",
            extra=extra,
        )
    return TestResult(name, 0.0, 0, True, note=note, extra=extra)


# ---------------------------------------------------------------- network (cached)


def fetch_pixels(
    tic_id: int,
    sector: int,
    root: Path,
    star_ra: float,
    star_dec: float,
    pmra_mas_yr: float | None = None,
    pmdec_mas_yr: float | None = None,
) -> PixelData:
    """SPOC 2-min TPF for the sector, cached under <root>/cache/tpf.

    The TIC position (epoch J2000) is propagated with proper motion to the TPF mid-time
    before projecting it on the cutout (audit B4: up to ~1.3 px for 1"/yr stars by 2026).
    """
    import lightkurve as lk

    from planethunter.preprocess.clean import quality_bitmask

    cache = root / "cache" / "tpf"
    cache.mkdir(parents=True, exist_ok=True)
    sr = lk.search_targetpixelfile(
        f"TIC {tic_id}", mission="TESS", author="SPOC", exptime=120, sector=sector
    )
    if len(sr) == 0:
        raise LookupError(f"no SPOC 2-min TPF for TIC {tic_id} sector {sector}")
    tpf = sr[0].download(download_dir=str(cache), quality_bitmask="none")
    q = np.asarray(tpf.quality, dtype=np.int64)
    time = np.asarray(tpf.time.value, dtype=float)
    ra, dec = propagate_position(
        star_ra,
        star_dec,
        pmra_mas_yr,
        pmdec_mas_yr,
        TIC_EPOCH_JYEAR,
        btjd_to_jyear(float(np.nanmedian(time))),
    )
    x, y = tpf.wcs.all_world2pix(ra, dec, 0)
    return PixelData(
        time=time,
        flux=np.asarray(tpf.flux.value, dtype=float),
        quality_ok=(q & quality_bitmask("default")) == 0,
        aperture=np.asarray(tpf.pipeline_mask, dtype=bool),
        target_xy=(float(x), float(y)),
        sector=sector,
        origin=(int(tpf.column), int(tpf.row)),
        wcs=tpf.wcs,
    )


GAIA_COLUMNS = ["Source", "RA_ICRS", "DE_ICRS", "Gmag", "BP-RP", "pmRA", "pmDE"]


def match_gaia_target(
    df: pd.DataFrame,
    ra: float,
    dec: float,
    *,
    pmra_mas_yr: float | None = None,
    pmdec_mas_yr: float | None = None,
    tmag: float | None = None,
    radius_arcsec: float = 3.0,
) -> tuple[pd.DataFrame, float | None, str]:
    """Identify the target among Gaia DR3 sources; return (neighbors, target T, note).

    The TIC position (J2000) is propagated to the Gaia epoch (2016.0) first. Among sources
    within `radius_arcsec`, the one whose converted T is closest to the TIC Tmag wins (the
    brightest if Tmag is unknown). If none matches, the TIC Tmag is used for the target and
    no source is dropped. `sep_arcsec` is measured from the propagated position.
    """
    from planethunter.catalogs.mirrors import angular_sep_arcsec

    if df.empty:
        return df.assign(sep_arcsec=[]), tmag, "no Gaia sources"
    ra16, dec16 = propagate_position(
        ra, dec, pmra_mas_yr, pmdec_mas_yr, TIC_EPOCH_JYEAR, GAIA_DR3_EPOCH_JYEAR
    )
    df = df.copy()
    df["sep_arcsec"] = angular_sep_arcsec(
        ra16, dec16, df["RA_ICRS"].to_numpy(float), df["DE_ICRS"].to_numpy(float)
    )
    df["Tmag"] = gaia_g_to_tmag(df["Gmag"], df.get("BP-RP"))
    near = df[(df["sep_arcsec"] < radius_arcsec) & np.isfinite(df["Tmag"])]
    if tmag is not None and np.isfinite(tmag) and len(near):
        dt = (near["Tmag"] - tmag).abs()
        near = near[dt < 1.5].assign(_dt=dt[dt < 1.5]).sort_values("_dt")
    else:
        near = near.sort_values("Tmag")
    if near.empty:
        return df, tmag, "target not matched in Gaia; TIC Tmag used for the target"
    target = near.index[0]
    return df.drop(index=target), float(df.loc[target, "Tmag"]), ""


def fetch_gaia_neighbors(
    tic_id: int,
    ra: float,
    dec: float,
    root: Path,
    radius_arcsec: float = 2.5 * PIXEL_ARCSEC,
    *,
    pmra_mas_yr: float | None = None,
    pmdec_mas_yr: float | None = None,
    tmag: float | None = None,
) -> tuple[pd.DataFrame, float | None, str]:
    """Gaia DR3 sources (VizieR) within `radius_arcsec`. Returns (neighbors, target T, note)."""
    cache = root / "cache" / "gaia" / f"tic{tic_id}_v2.parquet"
    if cache.exists():
        df = pd.read_parquet(cache)
    else:
        import astropy.units as u
        from astropy.coordinates import SkyCoord
        from astroquery.vizier import Vizier

        v = Vizier(columns=GAIA_COLUMNS, row_limit=-1)
        res = v.query_region(
            SkyCoord(ra * u.deg, dec * u.deg), radius=radius_arcsec * u.arcsec, catalog=GAIA_VIZIER
        )
        if len(res):
            tab = res[0]
            df = tab.to_pandas()
            df["Source"] = [_gaia_id(x) for x in np.asarray(tab["Source"], dtype=np.int64)]
        else:
            df = pd.DataFrame(columns=GAIA_COLUMNS)
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache, index=False)
    return match_gaia_target(
        df, ra, dec, pmra_mas_yr=pmra_mas_yr, pmdec_mas_yr=pmdec_mas_yr, tmag=tmag
    )


# ---------------------------------------------------------------- 12: other sectors


def _bls_best(t: np.ndarray, f: np.ndarray, dy: float, periods: np.ndarray, durs: list[float]):
    """(SNR, depth ppm, period d, t0 BTJD) of the best BLS peak."""
    from astropy.timeseries import BoxLeastSquares

    res = BoxLeastSquares(t, f, dy=np.full_like(f, dy)).power(periods, durs, objective="snr")
    i = int(np.nanargmax(res.depth_snr))
    return (
        float(res.depth_snr[i]),
        float(res.depth[i] * 1e6),
        float(res.period[i]),
        float(res.transit_time[i]),
    )


def sector_presence(
    time: np.ndarray,
    flux: np.ndarray,
    period: float,
    duration_days: float,
    depth_ppm: float,
    *,
    rel_window: float = 0.01,
    null_trials: int = 40,
    seed: int = 0,
) -> dict:
    """Look for the signal in another sector: BLS over a narrow range around P and 2P.

    Also measures the star's own noise floor: the same search at `null_trials` random
    periods away from P/2, P and 2P (90th percentile), on the light curve with the best
    P/2P peak masked (|phase| < 1 T14 at the P-equivalent period, which also covers 2P).
    Audit B3: with the signal left in, the floor tracked the signal (SNR 2192 vs floor 2272)
    and 16 of 24 failures were false. Measured over 144 trials in sector 69 (before masking):
    the SNR found in noise has median 5.2, p90 19 and p99 98; a fixed threshold does not work.
    """
    ok = np.isfinite(time) & np.isfinite(flux)
    t, f = time[ok], flux[ok]
    nan = float("nan")
    if len(t) < 200:
        return {"expected_snr": nan, "snr": nan, "depth_ppm": nan, "floor": nan}
    span = t.max() - t.min()
    p2p = float(np.std(np.diff(f)) / math.sqrt(2))
    n_in = len(t) * duration_days / period
    expected = depth_ppm * 1e-6 / p2p * math.sqrt(max(n_in, 1.0)) if p2p > 0 else nan

    def grid(p0: float) -> np.ndarray:
        parts = [
            np.linspace(k * p0 * (1 - rel_window), k * p0 * (1 + rel_window), 300)
            for k in (1, 2)
            if k * p0 < 0.9 * span
        ]
        return np.concatenate(parts) if parts else np.array([])

    periods = grid(period)
    durs = [d for d in (0.7 * duration_days, duration_days, 1.3 * duration_days) if d < period / 2]
    if len(periods) == 0 or not durs or p2p <= 0:
        return {"expected_snr": expected, "snr": nan, "depth_ppm": nan, "floor": nan}
    snr, depth, best_p, best_t0 = _bls_best(t, f, p2p, periods, durs)
    # Mask the candidate signal before measuring the floor.
    p_eq = best_p / 2 if best_p > 1.5 * period else best_p
    keep = np.abs(phase_days(t, p_eq, best_t0)) > duration_days
    tn, fn = (t[keep], f[keep]) if keep.sum() >= 200 else (t, f)
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(null_trials):
        for _attempt in range(20):
            p_null = period * rng.uniform(0.6, 1.7)
            if all(abs(p_null / (k * period) - 1) > 0.05 for k in (0.5, 1, 2)):
                break
        g = grid(p_null)
        if len(g):
            null.append(_bls_best(tn, fn, p2p, g, durs)[0])
    floor = float(np.percentile(null, 90)) if null else nan
    return {
        "expected_snr": float(expected),
        "snr": snr,
        "depth_ppm": depth,
        "period": best_p,
        "floor": floor,
    }


def other_sectors_test(
    results: dict[int, dict],
    depth_ppm: float,
    *,
    blind: dict | None = None,
    min_expected: float = 10.0,
    min_snr: float = 7.0,
    blind_min_expected: float = 20.0,
) -> TestResult:
    """A real signal reappears in the other sectors; a single-sector systematic does not.

    Order of evidence:
    1. Blind search (same pipeline) in the other sectors recovers P, 2P or P/2: confirms.
    2. Decisive absence in >= 2 sectors (expected >= min_expected and >= 1.5 x the star's
       noise floor, and not detected): veto.
    3. Blind search does not recover it and combined expected SNR >= blind_min_expected: fail.
    4. Otherwise: inconclusive.
    Measured in sector 69: signal 1634 had expected 12 and 9 in s95/s96 with floors 13.5 and
    11.6; absence there is not evidence. The blind search in s95-97 found neither 11.35 d nor
    22.7 d.
    """
    name = "other_sectors"
    if not results and not blind:
        return TestResult(name, None, min_expected, None, note="no other sectors")
    seen, decisive_absent, parts = [], [], []
    for sec, r in sorted(results.items()):
        exp, floor = r["expected_snr"], r.get("floor", float("nan"))
        floor_ok = not np.isfinite(floor) or r["snr"] > floor
        det = (
            r["snr"] >= min_snr
            and r["depth_ppm"] >= 0.5 * depth_ppm
            and (not np.isfinite(exp) or r["snr"] >= 0.5 * exp)
            and floor_ok
        )
        decisive = exp >= min_expected and (not np.isfinite(floor) or exp >= 1.5 * floor)
        if det:
            seen.append(sec)
        elif decisive:
            decisive_absent.append(sec)
        parts.append(
            f"s{sec}: expected {exp:.0f}, found SNR {r['snr']:.1f} (floor {floor:.1f}, "
            f"{r['depth_ppm']:.0f} ppm){' detected' if det else ''}"
        )
    note = "; ".join(parts)
    if blind:
        note += f" | blind search: {blind['note']}"
        if blind["recovered"]:
            return TestResult(name, float(len(seen)), min_expected, True, note=note)
    if seen:
        ratios = [results[s]["depth_ppm"] / depth_ppm for s in seen]
        bad = [s for s, q in zip(seen, ratios, strict=True) if q > 2.0 or q < 0.5]
        if len(bad) * 2 > len(seen):
            return TestResult(
                name,
                float(len(seen)),
                min_expected,
                False,
                note=note + " — depth inconsistent across sectors",
            )
    if len(decisive_absent) >= 2 and not seen:
        return TestResult(
            name,
            0.0,
            min_expected,
            False,
            veto=True,
            note=note + " — absent where it should be clear: systematic",
        )
    if blind and not blind["recovered"] and blind.get("expected_total", 0) >= blind_min_expected:
        return TestResult(
            name, 0.0, min_expected, False, note=note + " — does not reappear in blind search"
        )
    if seen:
        return TestResult(name, float(len(seen)), min_expected, True, note=note)
    return TestResult(name, 0.0, min_expected, None, note=note + " — inconclusive")


# ---------------------------------------------------------------- SIMBAD and Gaia EB

# Current SIMBAD object-type codes (https://simbad.cds.unistra.fr/guide/otypes.htx).
SIMBAD_FAIL_OTYPES = ("EB*", "SB*", "El*")
# Informational only: variable, young or active stars (the transit can still be real).
SIMBAD_INFO_OTYPES = {
    "EB?",
    "SB?",
    "El?",
    "Em*",
    "Be*",
    "Ae*",
    "RotV*",
    "BY*",
    "RS*",
    "Ce*",
    "cC*",
    "RR*",
    "dS*",
    "Mi*",
    "LP*",
    "Y*O",
    "Y*?",
    "TT*",
    "TT?",
    "Or*",
    "Pu*",
    "s*r",
    "s*b",
    "s*y",
    "WR*",
    "V*",
    "Ir*",
    "Er*",
    "bC*",
    "gD*",
    "SX*",
}
SIMBAD_PLANET_OTYPES = ("Pl", "Pl?")


def fetch_simbad_type(ra: float, dec: float, radius_arcsec: float = 5.0) -> tuple[str, str] | None:
    """(main_id, otype) of the nearest non-planet SIMBAD object within `radius_arcsec`.

    Planet entries (otype Pl) share the host's position and are skipped. None if nothing.
    """
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.simbad import Simbad

    s = Simbad()
    s.add_votable_fields("otype")
    t = s.query_region(SkyCoord(ra * u.deg, dec * u.deg), radius=radius_arcsec * u.arcsec)
    if t is None or len(t) == 0:
        return None
    cols = {c.lower(): c for c in t.colnames}
    otypes = np.array([str(x).strip() for x in t[cols.get("otype", "otype")]])
    ids = np.array([str(x) for x in t[cols.get("main_id", "main_id")]])
    order = np.arange(len(t))
    ra_c, de_c = cols.get("ra"), cols.get("dec")
    if ra_c and de_c:
        from planethunter.catalogs.mirrors import angular_sep_arcsec

        sep = angular_sep_arcsec(ra, dec, np.asarray(t[ra_c], float), np.asarray(t[de_c], float))
        order = np.argsort(np.where(np.isfinite(sep), sep, np.inf))
    for i in order:
        if otypes[i] not in SIMBAD_PLANET_OTYPES:
            return ids[i], otypes[i]
    return None


def simbad_test(
    found: tuple[str, str] | None, fail_otypes: tuple[str, ...] | list[str] = SIMBAD_FAIL_OTYPES
) -> TestResult:
    """Fail only on eclipsing/spectroscopic/ellipsoidal binaries; other types are informational."""
    name = "simbad_type"
    if found is None:
        return TestResult(name, None, None, None, note='no SIMBAD object within 5"')
    main_id, otype = found
    if otype in SIMBAD_PLANET_OTYPES:
        return TestResult(name, None, None, None, note=f"{main_id}: planet entry only")
    bad = otype in fail_otypes
    info = otype in SIMBAD_INFO_OTYPES
    return TestResult(
        name,
        None,
        None,
        not bad,
        note=f"{main_id}: type {otype}"
        + (" (binary: suspect)" if bad else " (variable/young: informational)" if info else ""),
    )


GAIA_EB_VIZIER = "I/358/veb"  # Gaia DR3 eclipsing binaries (~2.2 million); incomplete


def fetch_gaia_eb(ra: float, dec: float, radius_arcsec: float = PIXEL_ARCSEC) -> pd.DataFrame:
    """Gaia DR3 eclipsing binaries within `radius_arcsec` (columns Source, period_days, sep)."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astroquery.vizier import Vizier

    v = Vizier(row_limit=20, columns=["Source", "RA_ICRS", "DE_ICRS", "Freq"])
    res = v.query_region(
        SkyCoord(ra * u.deg, dec * u.deg), radius=radius_arcsec * u.arcsec, catalog=GAIA_EB_VIZIER
    )
    if not len(res):
        return pd.DataFrame(columns=["Source", "period_days", "sep_arcsec"])
    tab = res[0]
    df = tab.to_pandas()
    df["Source"] = [_gaia_id(x) for x in np.asarray(tab["Source"], dtype=np.int64)]
    from planethunter.catalogs.mirrors import angular_sep_arcsec

    df["period_days"] = 1.0 / df["Freq"]
    df["sep_arcsec"] = angular_sep_arcsec(
        ra, dec, df["RA_ICRS"].to_numpy(), df["DE_ICRS"].to_numpy()
    )
    return df


def gaia_eb_test(ebs: pd.DataFrame, period: float, rel_tol: float = 0.02) -> TestResult:
    """Gaia EB in the target pixel: veto if the period is compatible (aliases 1, 2, 1/2)."""
    name = "gaia_eb"
    if ebs is None or ebs.empty:
        return TestResult(
            name, 0, None, True, note='no Gaia DR3 EB within 21" (incomplete catalog)'
        )
    for r in ebs.itertuples():
        for k in (1.0, 2.0, 0.5):
            if abs(period / (k * r.period_days) - 1) < rel_tol:
                return TestResult(
                    name,
                    float(r.sep_arcsec),
                    None,
                    False,
                    veto=True,
                    note=f'Gaia DR3 EB {_gaia_id(r.Source)} at {r.sep_arcsec:.1f}" '
                    f"with P = {r.period_days:.4f} d (alias {k:g} of the signal)",
                )
    # .loc[i, column] keeps each column's dtype; a whole row (iloc) would cast int64 IDs to float.
    i = ebs["sep_arcsec"].astype(float).idxmin()
    sep, per = float(ebs.loc[i, "sep_arcsec"]), float(ebs.loc[i, "period_days"])
    return TestResult(
        name,
        sep,
        None,
        False,
        note=f'Gaia DR3 EB {_gaia_id(ebs.loc[i, "Source"])} at {sep:.1f}" '
        f"(P = {per:.4f} d, different period)",
    )


# ---------------------------------------------------------------- 13: FPP (triceratops)

FPP_DIR = Path(__file__).resolve().parents[3] / "tools" / "fpp"


def run_fpp(
    *,
    tic_id: int,
    sectors: list[int],
    depth_ppm: float,
    period_days: float,
    duration_days: float,
    apertures: dict[int, list[list[int]]],
    phase_days: np.ndarray,
    flux: np.ndarray,
    flux_err: np.ndarray,
    workdir: Path,
    exptime_days: float = 120 / 86400,
    dilution_corrected: bool = True,
    n_draws: int = 1_000_000,
    repeats: int = 3,
    timeout_s: int = 1800,
) -> dict:
    """Run tools/fpp/run_fpp.py in the isolated environment. Never raises: errors go in 'error'.

    `phase_days`, `flux`, `flux_err`: folded light curve (days from mid-transit, normalized
    flux). `exptime_days`: cadence of that light curve (supersampling in triceratops).
    `dilution_corrected`: True for PDCSAP (crowding-corrected), False for SAP/aperture flux.
    Output: ok, fpp, nfpp (means over `repeats`), fpp_std, nfpp_std, scenarios, error.
    """
    import hashlib
    import json
    import subprocess

    workdir = workdir.resolve()  # absolute paths: the subprocess runs inside workdir
    workdir.mkdir(parents=True, exist_ok=True)
    np.savez(workdir / "lc.npz", phase_days=phase_days, flux=flux, flux_err=flux_err)
    inp, out = workdir / "in.json", workdir / "out.json"
    # Only sectors with an aperture: triceratops pairs apertures and sectors by position.
    secs = sorted(int(s) for s in sectors if int(s) in apertures)
    payload = json.dumps(
        {
            "tic_id": tic_id,
            "sectors": secs,
            "depth": depth_ppm * 1e-6,
            "period_days": period_days,
            "duration_days": duration_days,
            "apertures": {str(k): apertures[k] for k in secs},
            "lc_npz": str(workdir / "lc.npz"),
            "n_draws": n_draws,
            "repeats": repeats,
            "exptime_days": exptime_days,
            "dilution_corrected": dilution_corrected,
            "cache_dir": str(workdir.parent / "lk_cache"),
            # light-curve fingerprint: the cache is only valid for the same data
            "lc_sha": hashlib.sha256(
                np.ascontiguousarray(np.r_[phase_days, flux, flux_err]).tobytes()
            ).hexdigest(),
        }
    )
    if not secs:
        return {"ok": False, "error": "no sector with an aperture"}
    # Same input (including the light curve) and a good result on disk: reuse it (~6 min saved).
    if inp.exists() and out.exists() and inp.read_text(encoding="utf-8") == payload:
        cached = json.loads(out.read_text(encoding="utf-8"))
        if cached.get("ok"):
            return cached
    inp.write_text(payload, encoding="utf-8")
    out.unlink(missing_ok=True)
    try:
        proc = subprocess.run(
            [
                "uv",
                "run",
                "--project",
                str(FPP_DIR),
                "python",
                str(FPP_DIR / "run_fpp.py"),
                str(inp),
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=timeout_s * max(1, repeats),
            # triceratops writes *_gaia_background.csv to the current directory: keep it in cache
            cwd=str(workdir),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout after {timeout_s * max(1, repeats)} s"}
    except FileNotFoundError:
        return {"ok": False, "error": "uv not found on PATH"}
    if not out.exists():
        return {"ok": False, "error": f"no output (exit {proc.returncode}): {proc.stderr[-300:]}"}
    return json.loads(out.read_text(encoding="utf-8"))


def fpp_test(
    res: dict,
    *,
    rp_rearth: float | None = None,
    snr: float | None = None,
    exptime_min: float | None = None,
    candidate_max: float = 0.5,
    nfpp_fail: float = 0.1,
    nfpp_veto: float = 0.5,
    validated_fpp: float = 0.015,
    validated_nfpp: float = 1e-3,
    region_max_rp: float = 8.0,
    region_min_snr: float = 15.0,
    region_max_exptime_min: float = 2.0,
) -> TestResult:
    """Interpret triceratops FPP/NFPP (Giacalone et al. 2021).

    Fail if FPP >= candidate_max (likely false positive) or NFPP > nfpp_fail ("likely nearby
    false positive"). Veto if NFPP > nfpp_veto: most of the posterior sits on a resolved Gaia
    neighbor, which no follow-up of the target would change. FPP < 0.015 and NFPP < 1e-3 =
    validation level, but the classes hold only for Rp < 8 R_earth, SNR >= 15 and 2-min data
    (30-min FFI data has no confident validation region). The region flags go in `extra`
    (keys in_validation_region, rp_ok, snr_ok, cadence_ok, validated, likely_planet,
    likely_nearby_fp) and in the note; severity reads `extra`.
    """
    name = "fpp_triceratops"
    if not res.get("ok"):
        return TestResult(
            name, None, candidate_max, None, note=f"FPP failed: {res.get('error', '')}"[:250]
        )
    fpp, nfpp = float(res["fpp"]), float(res["nfpp"])
    rp_ok = rp_rearth is not None and np.isfinite(rp_rearth) and rp_rearth < region_max_rp
    snr_ok = snr is not None and np.isfinite(snr) and snr >= region_min_snr
    cad_ok = exptime_min is not None and exptime_min <= region_max_exptime_min + 1e-6
    region = bool(rp_ok and snr_ok and cad_ok)
    validated = region and fpp < validated_fpp and nfpp < validated_nfpp
    likely_planet = fpp < candidate_max and nfpp < validated_nfpp
    nearby_fp = nfpp > nfpp_fail
    top = ", ".join(f"{s['scenario']} {s['prob']:.2f}" for s in res.get("scenarios", [])[:3])
    level = (
        "likely nearby false positive"
        if nearby_fp
        else "validation level (requires high-resolution imaging)"
        if fpp < validated_fpp and nfpp < validated_nfpp
        else "plausible candidate"
        if fpp < candidate_max
        else "likely false positive"
    )
    std = ""
    if res.get("repeats", 1) > 1:
        std = (
            f" (mean of {res['repeats']}; std {res.get('fpp_std', float('nan')):.2g}/"
            f"{res.get('nfpp_std', float('nan')):.2g})"
        )
    flags = (
        f"region: Rp<{region_max_rp:g} {'yes' if rp_ok else 'no'}, "
        f"SNR>={region_min_snr:g} {'yes' if snr_ok else 'no'}, "
        f"2-min {'yes' if cad_ok else 'no'}"
    )
    if not region:
        level += "; outside the validation region"
    return TestResult(
        name,
        fpp,
        candidate_max,
        fpp < candidate_max and not nearby_fp,
        veto=nfpp > nfpp_veto,
        note=f"FPP {fpp:.3g}, NFPP {nfpp:.3g}{std}: {level}. {flags}. Scenarios: {top}",
        extra={
            "fpp": fpp,
            "nfpp": nfpp,
            "fpp_std": res.get("fpp_std"),
            "nfpp_std": res.get("nfpp_std"),
            "repeats": res.get("repeats", 1),
            "rp_rearth": rp_rearth,
            "snr": snr,
            "exptime_min": exptime_min,
            "rp_ok": bool(rp_ok),
            "snr_ok": bool(snr_ok),
            "cadence_ok": bool(cad_ok),
            "in_validation_region": region,
            "validated": bool(validated),
            "likely_planet": bool(likely_planet),
            "likely_nearby_fp": bool(nearby_fp),
        },
    )
