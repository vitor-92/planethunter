"""Compute FPP/NFPP with triceratops (Giacalone+2021) in an isolated environment.

Usage: uv run --project tools/fpp python tools/fpp/run_fpp.py input.json output.json

input.json:
  tic_id, sectors [int] (only sectors that have an aperture), depth (fraction), period_days,
  duration_days (T14, for the out-of-transit scatter), apertures {"<sector>": [[column, row]]},
  lc_npz (file with phase_days, flux, flux_err), n_draws (default 1_000_000),
  repeats (default 3), exptime_days (cadence of the light curve, default 2 min),
  dilution_corrected (true for PDCSAP, false for SAP), cache_dir (optional)
output.json:
  ok, fpp, nfpp (means), fpp_std, nfpp_std, fpp_runs, nfpp_runs, repeats, flux_err_0,
  scenarios [{scenario, tic, prob}], params_estimated, error

Rules (audit A4, 2026-10-10):
- flux_err_0 = max(median pipeline error, 1.4826 MAD of the out-of-transit flux): the
  pipeline error underestimated the real scatter by 1.9-46x in the four FPP = 1.000 cases.
- ok = False if the target row lacks mass, radius, Teff or parallax (triceratops then stops
  its scenario loop and the probabilities are meaningless), or if FPP_degenerate is set.
- One aperture per sector actually loaded by triceratops (a sector that fails to download
  is skipped inside triceratops and would misalign apertures and sectors).
"""

from __future__ import annotations

import json
import sys
import traceback
import warnings

TARGET_REQUIRED = ("mass", "rad", "Teff", "plx")


def flux_err_0(phase_days, flux, flux_err, duration_days: float | None) -> float:
    """max(median(flux_err), 1.4826 MAD of the flux with |phase| > 0.75 T14)."""
    import numpy as np

    phase_days, flux = np.asarray(phase_days, float), np.asarray(flux, float)
    err = np.asarray(flux_err, float)
    med_err = float(np.nanmedian(err)) if np.isfinite(err).any() else 0.0
    if duration_days and duration_days > 0:
        oot = np.abs(phase_days) > 0.75 * duration_days
    else:
        oot = np.ones(len(flux), dtype=bool)
    f = flux[oot & np.isfinite(flux)]
    mad = 1.4826 * float(np.median(np.abs(f - np.median(f)))) if len(f) >= 10 else 0.0
    return max(med_err, mad)


def target_problem(stars) -> str | None:
    """Reason why the target row (first row of target.stars) cannot be validated, or None."""
    import numpy as np

    row = stars.iloc[0]
    missing = [
        c for c in TARGET_REQUIRED if c not in stars.columns or not np.isfinite(float(row[c]))
    ]
    if missing:
        return f"target star lacks {', '.join(missing)}"
    return None


def summarize(runs: list[tuple[float, float]]) -> dict:
    """Mean and standard deviation of FPP and NFPP over repeated runs."""
    import numpy as np

    fpp = np.array([r[0] for r in runs], float)
    nfpp = np.array([r[1] for r in runs], float)
    return {
        "fpp": float(fpp.mean()),
        "nfpp": float(nfpp.mean()),
        "fpp_std": float(fpp.std(ddof=1)) if len(fpp) > 1 else 0.0,
        "nfpp_std": float(nfpp.std(ddof=1)) if len(nfpp) > 1 else 0.0,
        "fpp_runs": fpp.tolist(),
        "nfpp_runs": nfpp.tolist(),
        "repeats": len(runs),
    }


def compute(cfg: dict, target_factory) -> dict:
    """Run triceratops for `cfg`; `target_factory(ID, sectors, cache_dir)` builds the target.

    Separated from main() so that it can be unit-tested with a mock target.
    """
    import numpy as np

    sectors = np.array(sorted(int(s) for s in cfg["sectors"] if str(s) in cfg["apertures"]))
    if len(sectors) == 0:
        return {"ok": False, "error": "no sector with an aperture"}
    target = target_factory(int(cfg["tic_id"]), sectors, cfg.get("cache_dir"))
    aps = [np.array(cfg["apertures"][str(s)]) for s in sectors]
    n_pix = len(getattr(target, "pix_coords", []))
    if n_pix != len(aps):
        return {
            "ok": False,
            "error": f"triceratops loaded {n_pix} sector(s) for {len(aps)} aperture(s): "
            "a sector failed inside triceratops; apertures would be misaligned",
        }
    dil = bool(cfg.get("dilution_corrected", True))
    target.calc_depths(tdepth=float(cfg["depth"]), all_ap_pixels=aps, dilution_corrected=dil)
    problem = target_problem(target.stars)
    if problem:
        return {"ok": False, "error": problem}
    lc = np.load(cfg["lc_npz"])
    err0 = flux_err_0(lc["phase_days"], lc["flux"], lc["flux_err"], cfg.get("duration_days"))
    runs, probs = [], None
    for _ in range(max(1, int(cfg.get("repeats", 3)))):
        target.calc_probs(
            time=lc["phase_days"],
            flux_0=lc["flux"],
            flux_err_0=err0,
            P_orb=float(cfg["period_days"]),
            N=int(cfg.get("n_draws", 1_000_000)),
            exptime=float(cfg.get("exptime_days", 120 / 86400)),
            dilution_corrected=dil,
            verbose=0,
        )
        if getattr(target, "FPP_degenerate", False):
            return {
                "ok": False,
                "error": "FPP degenerate (every draw geometrically invalid or NaN evidences)",
                "flux_err_0": err0,
            }
        runs.append((float(target.FPP), float(target.NFPP)))
        probs = target.probs
    top = probs.sort_values("prob", ascending=False).head(5)
    est = ""
    if "params_estimated" in target.stars.columns:
        est = str(target.stars["params_estimated"].iloc[0] or "")
    return {
        "ok": True,
        **summarize(runs),
        "flux_err_0": err0,
        "params_estimated": est,
        "scenarios": [
            {"scenario": str(r["scenario"]), "tic": str(r["ID"]), "prob": float(r["prob"])}
            for _, r in top.iterrows()
        ],
    }


def main(inp: str, out: str) -> None:
    with open(inp, encoding="utf-8") as fh:
        cfg = json.loads(fh.read())
    try:
        warnings.simplefilter("ignore")
        from triceratops import triceratops as tr

        def factory(tic_id, sectors, cache_dir):
            return tr.target(ID=tic_id, sectors=sectors, lightkurve_cache_dir=cache_dir)

        result = compute(cfg, factory)
    except Exception as exc:  # the caller treats this as "no data"
        result = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "trace": traceback.format_exc()[-2000:],
        }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
