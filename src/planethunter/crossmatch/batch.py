"""Batch crossmatch over DataFrames: star selection + per-signal classification.

Pure functions (no network, no database). Used by `pipeline.run_crossmatch` and by the
alert gate (`alerts.notify`), which re-classifies each P0/P1 against fresh mirrors.

Star selection (step 1):
- exact TIC ID (integer) -> host, separation 0;
- position: the TIC position (epoch J2000) moves with the TIC proper motion. Catalog
  positions have mixed, often undocumented epochs (TIC/ExoFOP/Kepler J2000, Archive Gaia
  2015.5/2016, exoplanet.eu mostly J2000 from SIMBAD), so the separation used is the
  minimum distance between the catalog position and the target's track from J2000 to the
  observation epoch (the candidate T0). This only ever adds matches (protects against a
  false NEW on a high-proper-motion star) and is exact for any catalog epoch in between.
  Host: < host_radius_arcsec (21", 1 TESS pixel); neighbors: < nearby_radius_arcsec (2').
"""

from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from planethunter.config import CrossmatchConfig
from planethunter.crossmatch.core import CrossmatchResult, KnownObject, Source, classify

TIC_EPOCH_JYEAR = 2000.0
JD_J2000 = 2451545.0
BTJD_OFFSET = 2457000.0


def btjd_to_jyear(t_btjd: float) -> float:
    return 2000.0 + (t_btjd + BTJD_OFFSET - JD_J2000) / 365.25


class KnownCatalog:
    """Column arrays of the union of mirrors, for fast per-target selection."""

    def __init__(self, known: pd.DataFrame) -> None:
        self.df = known.reset_index(drop=True)
        self.ra = pd.to_numeric(self.df["ra_deg"], errors="coerce").to_numpy(float)
        self.dec = pd.to_numeric(self.df["dec_deg"], errors="coerce").to_numpy(float)
        tic = self.df["tic_id"].astype("Int64")
        mask = tic.notna().to_numpy()
        idx = pd.Series(np.flatnonzero(mask), index=tic[mask].astype("int64").to_numpy())
        self.by_tic: dict[int, np.ndarray] = {int(k): g.to_numpy() for k, g in idx.groupby(level=0)}

    def obj(self, i: int, sep: float) -> KnownObject:
        r = self.df.iloc[i]

        def f(x: object) -> float | None:
            return None if pd.isna(x) else float(x)  # type: ignore[arg-type]

        return KnownObject(
            source=Source(r["source"]),
            name=str(r["name"]),
            tic_id=None if pd.isna(r["tic_id"]) else int(r["tic_id"]),
            period_days=f(r["period_days"]),
            t0_btjd=f(r["t0_btjd"]),
            period_err_days=f(r["period_err_days"]),
            disposition=None if pd.isna(r["disposition"]) else str(r["disposition"]),
            separation_arcsec=float(sep),
        )


def track_separation_arcsec(
    ra: float,
    dec: float,
    pmra_mas_yr: float | None,
    pmdec_mas_yr: float | None,
    dt_years: float,
    ra_k: np.ndarray,
    dec_k: np.ndarray,
) -> np.ndarray:
    """Minimum distance (arcsec) between catalog points and the target's linear track.

    Track: from (ra, dec) at the TIC epoch to (ra, dec) + mu x dt_years. Tangent-plane
    approximation, valid for the <= 2' radii used here. pmra is mu_alpha* (includes cos dec).
    """
    xi = ((ra_k - ra + 180.0) % 360.0 - 180.0) * math.cos(math.radians(dec)) * 3600.0
    eta = (dec_k - dec) * 3600.0
    pmra = pmra_mas_yr if pmra_mas_yr is not None and math.isfinite(pmra_mas_yr) else 0.0
    pmdec = pmdec_mas_yr if pmdec_mas_yr is not None and math.isfinite(pmdec_mas_yr) else 0.0
    dx, dy = pmra * dt_years / 1000.0, pmdec * dt_years / 1000.0
    d2 = dx * dx + dy * dy
    if d2 <= 0:
        return np.hypot(xi, eta)
    s = np.clip((xi * dx + eta * dy) / d2, 0.0, 1.0)
    return np.hypot(xi - s * dx, eta - s * dy)


def select_objects(
    cat: KnownCatalog,
    tic_id: int,
    ra: float | None,
    dec: float | None,
    cfg: CrossmatchConfig,
    *,
    pmra_mas_yr: float | None = None,
    pmdec_mas_yr: float | None = None,
    t_obs_btjd: float | None = None,
) -> tuple[list[KnownObject], list[KnownObject]]:
    """(host objects, nearby objects) for one target. Separation in arcsec."""
    n = len(cat.ra)
    sep = np.full(n, np.inf)
    same = cat.by_tic.get(int(tic_id), np.array([], dtype=int))
    if ra is not None and dec is not None and math.isfinite(ra) and math.isfinite(dec) and n:
        from planethunter.catalogs.mirrors import angular_sep_arcsec

        sep0 = angular_sep_arcsec(float(ra), float(dec), cat.ra, cat.dec)
        dt = btjd_to_jyear(t_obs_btjd) - TIC_EPOCH_JYEAR if t_obs_btjd is not None else 0.0
        pm = math.hypot(
            pmra_mas_yr if pmra_mas_yr is not None and math.isfinite(pmra_mas_yr) else 0.0,
            pmdec_mas_yr if pmdec_mas_yr is not None and math.isfinite(pmdec_mas_yr) else 0.0,
        )
        reach = cfg.nearby_radius_arcsec + pm * abs(dt) / 1000.0 + 1.0
        cand = np.flatnonzero(np.nan_to_num(sep0, nan=np.inf) < reach)
        if len(cand):
            sep[cand] = track_separation_arcsec(
                float(ra), float(dec), pmra_mas_yr, pmdec_mas_yr, dt, cat.ra[cand], cat.dec[cand]
            )
    sep[same] = 0.0
    host_idx = np.flatnonzero(sep < cfg.host_radius_arcsec)
    near_idx = np.flatnonzero((sep >= cfg.host_radius_arcsec) & (sep < cfg.nearby_radius_arcsec))
    host = [cat.obj(int(i), sep[i]) for i in host_idx]
    near = [cat.obj(int(i), sep[i]) for i in near_idx]
    return host, near


def _f(x: object) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def result_row(signal_id: int, res: CrossmatchResult) -> dict:
    """One `crossmatch` table row (without run-level flags, ages and checked_at)."""
    best = res.matched[0] if res.matched else None
    pm = best[1] if best else None
    return {
        "signal_id": int(signal_id),
        "match_class": res.match_class.value,
        "host_known": res.host_known,
        "matched_name": best[0].name if best else None,
        "matched_source": best[0].source.value if best else None,
        "alias": str(pm.alias) if pm else None,
        "phase_consistent": pm.phase_consistent if pm else None,
        "phase_checked": res.phase_checked,
        "match_type": res.match_type,
        "host_eb": res.host_eb,
        "separation_arcsec": best[0].separation_arcsec if best else None,
        "n_host_objects": res.host_objects_checked,
        "n_nearby_objects": res.nearby_objects_checked,
        "notes": " | ".join(res.notes),
    }


def classify_frame(
    sigs: pd.DataFrame,
    known: pd.DataFrame | KnownCatalog,
    ages: dict[Source, float | None],
    cfg: CrossmatchConfig,
    *,
    keep_results: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict[int, CrossmatchResult]]:
    """Classify every signal of `sigs` (columns: signal_id, tic_id, period_days,
    period_err_days, t0_btjd, duration_hours, transit_times_json, ra_deg, dec_deg and
    optionally pmra_mas_yr, pmdec_mas_yr)."""
    cat = known if isinstance(known, KnownCatalog) else KnownCatalog(known)
    rows, results = [], {}
    for tic, grp in sigs.groupby("tic_id", sort=False):
        first = grp.iloc[0]
        t_obs = _f(grp["t0_btjd"].median())
        host, near = select_objects(
            cat,
            int(tic),
            _f(first.get("ra_deg")),
            _f(first.get("dec_deg")),
            cfg,
            pmra_mas_yr=_f(first.get("pmra_mas_yr")),
            pmdec_mas_yr=_f(first.get("pmdec_mas_yr")),
            t_obs_btjd=t_obs,
        )
        for _, s in grp.iterrows():
            tts = s.get("transit_times_json")
            tts = json.loads(tts) if isinstance(tts, str) and tts else None
            dur = _f(s.get("duration_hours"))
            res = classify(
                float(s["period_days"]),
                _f(s["t0_btjd"]),
                host,
                near,
                ages,
                cfg,
                transit_times=tts,
                duration_days=dur / 24.0 if dur else None,
                period_err_days=_f(s.get("period_err_days")),
            )
            rows.append(result_row(int(s["signal_id"]), res))
            if keep_results:
                results[int(s["signal_id"])] = res
    out = pd.DataFrame(rows)
    return (out, results) if keep_results else out
