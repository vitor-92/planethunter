"""Run-level systematics (audit A8): common-epoch spikes and signals shared between targets.

Pure functions over the run's signals table (joined with targets for position and Tmag).
No network, no database. Called by `pipeline.run_crossmatch`; the results go to the
crossmatch columns `epoch_spike_frac` and `shared_signal_{tic,sep_arcsec,role}`.

1. Epoch spikes. Spacecraft systematics (momentum dumps, scattered light, orbit-start ramps)
   put "transits" on many unrelated targets at the same times. Sector 107: 10-11 bins of
   0.25 d held 84 transits of held-out targets against 2.9 expected by chance. Algorithm:
   - histogram of the transit mid-times of the run's few-transit signals
     (1 <= n_transits <= epoch_spike_max_transits; many-transit signals smear uniformly),
     counting DISTINCT targets per bin (a target contributes once per bin however many of
     its signals land there), on two grids offset by half a bin (spikes straddling an edge);
   - baseline = median count over occupied bins; a bin is a spike when the count of OTHER
     targets (leave-one-target-out: the signal's own target is removed) is
     >= max(median + z x 1.4826 MAD, factor x median, min_count). The MAD term adapts to
     the background: with the wider period range (2026-10-13) sector 107 has ~100 targets
     per bin, so a fixed 5x-median rule found no spike although the known spikes stood
     3.5x (25 sigma) above it;
   - epoch_spike_frac = fraction of the signal's observed transits inside a spike bin of
     either grid, set to 0 when fewer than epoch_spike_min_hits transits are inside (one
     unlucky transit must not suppress a real 2-transit planet). NULL when fewer than
     epoch_spike_min_targets targets contribute (runs of a single target or a handful: no
     statistics) or the signal has no transit times.
     Measured 2026-10-13 (z 6, factor 2, min_hits 2): s107 171 NEW flagged, 0 of 216
     known planets/TOIs; s69 83 NEW, 2 of 152 known. Old rule (5x median, 1 hit):
     s107 0 flagged; s69 399 NEW and 5 known.
   Severity treats epoch_spike_frac >= epoch_spike_max_frac (0.5) as a systematic.

2. Shared signals. The same period (ratio 1, 2 or 1/2 within
   clip(3 sigma_rel combined, 0.1 %, 1 %)) and T0 (residual on the shorter period
   <= 0.5 max(D) + 3 |m| sigma_P) on ANOTHER target of the run within
   shared_signal_radius_arcsec. The role says whether THIS star can be the source:
   - "duplicate": separation <= duplicate_radius_arcsec (2"): almost certainly one star
     listed twice (TIC duplicate/split phantom, Paegert+2021);
   - otherwise compare the eclipsed flux captured by each aperture. SPOC PDCSAP depths are
     already corrected for crowding (CROWDSAP), so delta_pdc = dF_ap / F_star,ap and the
     eclipsed flux in each aperture is dF = depth x F_star with F_star = 10^(-0.4 Tmag).
     A star can be the source only if the intrinsic depth it would need,
     delta_req = max(dF over the pair) / F_star, is <= 1 (physically possible), and the
     aperture centred on the true source captures the MOST eclipsed flux, so:
       * the star with the larger dF and delta_req <= 1 is the "source";
       * the other one is a "victim" (its dimming is leaked light from the partner);
       * if the two dF are comparable (smaller/larger > shared_signal_flux_ratio_max) at a
         separation larger than one TESS pixel, neither aperture is centred on the source
         (a third star between them is more likely): both are "victim".
   With several partners the strongest role wins: duplicate > victim > source. Missing
   depth or Tmag: role "source" (cannot be ruled out) with a note.
   Severity: duplicate/victim -> no alert; source -> capped at P2.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

from planethunter.config import CrossmatchConfig

ROLE_RANK = {"duplicate": 0, "victim": 1, "source": 2}
TESS_PIXEL_ARCSEC = 21.0


def _times(x: object) -> np.ndarray:
    if isinstance(x, str) and x:
        return np.asarray(json.loads(x), dtype=float)
    if isinstance(x, list | tuple | np.ndarray):
        return np.asarray(x, dtype=float)
    return np.array([], dtype=float)


def epoch_spikes(sigs: pd.DataFrame, cfg: CrossmatchConfig) -> tuple[pd.Series, pd.DataFrame]:
    """(epoch_spike_frac per signal_id, table of spike bins [grid, t_start, t_end, count]).

    `sigs` columns: signal_id, tic_id, transit_times_json.
    """
    times = {
        int(s): _times(t)
        for s, t in zip(sigs["signal_id"], sigs["transit_times_json"], strict=True)
    }
    tics = dict(zip(sigs["signal_id"].astype(int), sigs["tic_id"].astype("int64"), strict=True))
    frac = pd.Series(np.nan, index=pd.Index(list(times), name="signal_id"), dtype=float)
    contrib = [s for s, t in times.items() if 1 <= len(t) <= cfg.epoch_spike_max_transits]
    n_targets = len({tics[s] for s in contrib})
    empty = pd.DataFrame(columns=["grid", "t_start", "t_end", "count", "threshold"])
    if n_targets < cfg.epoch_spike_min_targets:
        return frac, empty
    width = cfg.epoch_spike_bin_days
    in_spike = {s: np.zeros(len(t), dtype=bool) for s, t in times.items()}
    spike_rows = []
    for grid, offset in enumerate((0.0, 0.5 * width)):
        pairs = pd.DataFrame(
            {
                "tic": np.concatenate([np.full(len(times[s]), tics[s]) for s in contrib]),
                "b": np.concatenate(
                    [np.floor((times[s] - offset) / width).astype(np.int64) for s in contrib]
                ),
            }
        ).drop_duplicates()
        counts = pairs.groupby("b").size()
        arr = counts.to_numpy()
        med = float(np.median(arr))
        mad = 1.4826 * float(np.median(np.abs(arr - med)))
        thr = max(
            med + cfg.epoch_spike_z * max(mad, math.sqrt(med)),
            cfg.epoch_spike_factor * med,
            float(cfg.epoch_spike_min_count),
        )
        own = set(
            zip(pairs["tic"].to_numpy().tolist(), pairs["b"].to_numpy().tolist(), strict=True)
        )
        cdict = counts.to_dict()
        for b, c in cdict.items():
            if c >= thr:
                spike_rows.append(
                    {
                        "grid": grid,
                        "t_start": b * width + offset,
                        "t_end": (b + 1) * width + offset,
                        "count": int(c),
                        "threshold": thr,
                    }
                )
        for s, t in times.items():
            if not len(t):
                continue
            bins = np.floor((t - offset) / width).astype(np.int64)
            tic = tics[s]
            for i, b in enumerate(bins.tolist()):
                c = cdict.get(b, 0) - (1 if (tic, b) in own else 0)
                if c >= thr:
                    in_spike[s][i] = True
    for s, flags in in_spike.items():
        if len(flags):
            hits = int(flags.sum())
            frac[s] = float(flags.mean()) if hits >= cfg.epoch_spike_min_hits else 0.0
    return frac, pd.DataFrame(spike_rows) if spike_rows else empty


def _neighbor_pairs(targets: pd.DataFrame, radius_arcsec: float) -> list[tuple[int, int, float]]:
    """(tic_a, tic_b, sep) for every ordered pair of distinct targets within the radius."""
    from planethunter.catalogs.mirrors import angular_sep_arcsec

    t = targets.dropna(subset=["ra_deg", "dec_deg"]).sort_values("dec_deg")
    tic = t["tic_id"].to_numpy(np.int64)
    ra = t["ra_deg"].to_numpy(float)
    dec = t["dec_deg"].to_numpy(float)
    r_deg = radius_arcsec / 3600.0
    out = []
    lo_all = np.searchsorted(dec, dec - r_deg, side="left")
    hi_all = np.searchsorted(dec, dec + r_deg, side="right")
    for i in range(len(t)):
        lo, hi = lo_all[i], hi_all[i]
        if hi - lo <= 1:
            continue
        idx = np.arange(lo, hi)
        idx = idx[idx != i]
        sep = angular_sep_arcsec(ra[i], dec[i], ra[idx], dec[idx])
        for j, s in zip(idx[sep <= radius_arcsec], sep[sep <= radius_arcsec], strict=True):
            if tic[j] != tic[i]:
                out.append((int(tic[i]), int(tic[j]), float(s)))
    return out


def same_signal(a: pd.Series, b: pd.Series, cfg: CrossmatchConfig) -> bool:
    """Same period (ratio 1, 2, 1/2) and T0 within uncertainties. Days, hours for duration."""
    pa, pb = float(a["period_days"]), float(b["period_days"])
    if not (pa > 0 and pb > 0):
        return False
    ea = float(a["period_err_days"]) if pd.notna(a.get("period_err_days")) else 0.0
    eb = float(b["period_err_days"]) if pd.notna(b.get("period_err_days")) else 0.0
    tol = min(
        max(3.0 * math.hypot(ea / pa, eb / pb), cfg.shared_signal_period_tol_min),
        cfg.shared_signal_period_tol_max,
    )
    r = pa / pb
    if not any(abs(r / k - 1.0) <= tol for k in (1.0, 2.0, 0.5)):
        return False
    ta, tb = a.get("t0_btjd"), b.get("t0_btjd")
    if pd.isna(ta) or pd.isna(tb):
        return False
    g, eg = (pa, ea) if pa <= pb else (pb, eb)
    dt = float(ta) - float(tb)
    m = round(dt / g)
    resid = abs(dt - m * g)
    da = float(a["duration_hours"]) / 24.0 if pd.notna(a.get("duration_hours")) else 0.0
    db = float(b["duration_hours"]) / 24.0 if pd.notna(b.get("duration_hours")) else 0.0
    return resid <= 0.5 * max(da, db) + 3.0 * abs(m) * eg


def _eclipsed_flux(s: pd.Series) -> float | None:
    """depth (fraction) x 10^(-0.4 Tmag): eclipsed flux captured by the aperture (relative)."""
    d, tm = s.get("depth_ppm"), s.get("tmag")
    if pd.isna(d) or pd.isna(tm) or float(d) <= 0:
        return None
    return float(d) * 1e-6 * 10 ** (-0.4 * float(tm))


def pair_role(
    me: pd.Series, partner: pd.Series, sep_arcsec: float, cfg: CrossmatchConfig
) -> tuple[str, str | None]:
    """(role of `me`, note). See the module docstring for the physics."""
    if sep_arcsec <= cfg.duplicate_radius_arcsec:
        return "duplicate", None
    f_me, f_pa = _eclipsed_flux(me), _eclipsed_flux(partner)
    if f_me is None or f_pa is None:
        return "source", "shared_signal_role_undetermined (missing depth or Tmag)"
    big = max(f_me, f_pa)
    flux_me = 10 ** (-0.4 * float(me["tmag"]))
    plausible = big / flux_me <= 1.0
    if f_me < f_pa or not plausible:
        return "victim", None
    if sep_arcsec > TESS_PIXEL_ARCSEC and f_pa / f_me > cfg.shared_signal_flux_ratio_max:
        return "victim", "comparable eclipsed flux in both apertures: third star likely"
    return "source", None


def shared_signals(sigs: pd.DataFrame, cfg: CrossmatchConfig) -> pd.DataFrame:
    """Per signal with a partner: shared_signal_tic, shared_signal_sep_arcsec,
    shared_signal_role, shared_signal_note.

    `sigs` columns: signal_id, tic_id, period_days, period_err_days, t0_btjd, duration_hours,
    depth_ppm, ra_deg, dec_deg, tmag.
    """
    cols = [
        "signal_id",
        "shared_signal_tic",
        "shared_signal_sep_arcsec",
        "shared_signal_role",
        "shared_signal_note",
    ]
    targets = sigs.drop_duplicates("tic_id")[["tic_id", "ra_deg", "dec_deg"]]
    pairs = _neighbor_pairs(targets, cfg.shared_signal_radius_arcsec)
    if not pairs:
        return pd.DataFrame(columns=cols)
    by_tic = {int(k): g for k, g in sigs.groupby("tic_id")}
    best: dict[int, tuple[tuple, dict]] = {}
    for ta, tb, sep in pairs:
        for _, a in by_tic[ta].iterrows():
            for _, b in by_tic[tb].iterrows():
                if not same_signal(a, b, cfg):
                    continue
                role, note = pair_role(a, b, sep, cfg)
                f_b = _eclipsed_flux(b) or 0.0
                # rank: strongest role; for victims the partner with the most eclipsed flux;
                # otherwise the nearest partner
                key = (ROLE_RANK[role], -f_b if role == "victim" else 0.0, sep)
                row = {
                    "signal_id": int(a["signal_id"]),
                    "shared_signal_tic": int(tb),
                    "shared_signal_sep_arcsec": sep,
                    "shared_signal_role": role,
                    "shared_signal_note": note,
                }
                sid = int(a["signal_id"])
                if sid not in best or key < best[sid][0]:
                    best[sid] = (key, row)
    return pd.DataFrame([r for _, r in best.values()], columns=cols)


def run_level_flags(sigs: pd.DataFrame, cfg: CrossmatchConfig) -> pd.DataFrame:
    """epoch_spike_frac + shared_signal_* for every signal of the run (one row each)."""
    frac, _ = epoch_spikes(sigs, cfg)
    out = pd.DataFrame({"signal_id": sigs["signal_id"].astype(int).to_numpy()})
    out["epoch_spike_frac"] = out["signal_id"].map(frac)
    shared = shared_signals(sigs, cfg)
    out = out.merge(shared, on="signal_id", how="left")
    out["shared_signal_tic"] = out["shared_signal_tic"].astype("Int64")
    return out
