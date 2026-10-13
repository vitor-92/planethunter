"""Recall benchmark: does the pipeline recover the known TOIs of a sector?

`build`: freezes the sector's TOI list (ExoFOP) into <data>/benchmark/sector_NNNN.csv.
`evaluate`: compares the signals of a run against that list.

Note: ExoFOP "Planet SNR" is multi-sector; the SNR in a single sector is lower. That is why the
default filter is SNR >= 10 and the reference recall is also measured per depth bin.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from planethunter.catalogs.mirrors import EXOFOP_TOI, _fetch_csv
from planethunter.config import REPO_ROOT, Config
from planethunter.crossmatch.core import match_period
from planethunter.db.store import connect
from planethunter.ingest.lightcurves import parquet_path, read_parquet

RECOVERY_ALIASES = {1.0, 2.0, 0.5}
WEAK_ALIASES = {3.0, 1 / 3, 1.5, 2 / 3}  # signal found, ambiguous period: counted separately
DEPTH_BINS = [0, 500, 1000, 3000, 10_000, math.inf]


def bench_path(root: Path, sector: int, kind: str = "planets") -> Path:
    """kind = planets (CP/KP/PC, recall) or fp (TFOPWG FP/FA, vetting validation)."""
    prefix = "sector" if kind == "planets" else f"{kind}_sector"
    return root / "benchmark" / f"{prefix}_{sector:04d}.csv"


def build(
    root: Path,
    sector: int,
    *,
    min_snr: float = 10.0,
    max_period_days: float = 13.0,
    kind: str = "planets",
) -> Path:
    raw = _fetch_csv(EXOFOP_TOI)
    sectors = raw["Sectors"].fillna("").astype(str).str.split(",")
    in_sector = sectors.apply(lambda xs: str(sector) in [x.strip() for x in xs])
    tfop = raw["TFOPWG Disposition"].fillna("").astype(str).str.strip()
    tess = raw["TESS Disposition"].fillna("").astype(str).str.strip()
    disp = tfop.where(tfop != "", tess)
    period = pd.to_numeric(raw["Period (days)"], errors="coerce")
    snr = pd.to_numeric(raw["Planet SNR"], errors="coerce")
    wanted = ["CP", "KP", "PC"] if kind == "planets" else ["FP", "FA"]
    if kind == "fp":
        disp = tfop  # only the TFOPWG decision counts as a confirmed false positive
    sel = (
        in_sector
        & disp.isin(wanted)
        & (snr >= min_snr)
        & (period > 0.5)
        & (period <= max_period_days)
    )
    bench = pd.DataFrame(
        {
            "tic_id": pd.to_numeric(raw.loc[sel, "TIC ID"]).astype("int64"),
            "toi": raw.loc[sel, "TOI"].astype(str),
            "disposition": disp[sel],
            "period_days": period[sel],
            "t0_btjd": pd.to_numeric(raw.loc[sel, "Epoch (BJD)"], errors="coerce") - 2457000.0,
            "depth_ppm": pd.to_numeric(raw.loc[sel, "Depth (ppm)"], errors="coerce"),
            "duration_hours": pd.to_numeric(raw.loc[sel, "Duration (hours)"], errors="coerce"),
            "planet_snr": snr[sel],
            "tmag": pd.to_numeric(raw.loc[sel, "TESS Mag"], errors="coerce"),
        }
    )
    dest = bench_path(root, sector, kind)
    dest.parent.mkdir(parents=True, exist_ok=True)
    bench.to_csv(dest, index=False)
    return dest


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    den = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def expected_snr(root: Path, cfg: Config, sector: int, toi: pd.Series) -> tuple[float, int]:
    """Expected SNR of a TOI from this sector alone: catalog depth / point-to-point noise
    * sqrt(in-transit points with data). Also returns the number of epochs with data.

    ExoFOP "Planet SNR" is multi-sector; in sector 69, 55 of 68 missed TOIs had expected
    SNR < 7 in one sector, i.e. no pipeline would find them with that data alone.
    """
    import numpy as np

    from planethunter.preprocess import flatten_adaptive

    p = parquet_path(root, sector, "SPOC", int(toi["tic_id"]))
    if not p.exists():
        return math.nan, 0
    df, _ = read_parquet(p)
    lc = flatten_adaptive(df, sector, cfg.preprocess)
    if len(lc) < 10:
        return math.nan, 0
    period, t0 = float(toi["period_days"]), float(toi["t0_btjd"])
    dur = float(toi["duration_hours"]) / 24.0 if pd.notna(toi["duration_hours"]) else 2.0 / 24
    phase = ((lc.time - t0 + 0.5 * period) % period) - 0.5 * period
    intr = np.abs(phase) < 0.5 * dur
    p2p = np.std(np.diff(lc.flux.astype(float))) / math.sqrt(2)
    n_in = int(intr.sum())
    n_epochs = len(np.unique(np.round((lc.time[intr] - t0) / period)))
    if n_in == 0 or p2p <= 0:
        return 0.0, n_epochs
    return float(toi["depth_ppm"]) * 1e-6 / p2p * math.sqrt(n_in), n_epochs


def evaluate(root: Path, cfg: Config, sector: int, run_id: str) -> pd.DataFrame:
    """One row per TOI with status: recovered, recovered_alias, period_only, missed, no_data.

    Column `detectable`: expected single-sector SNR >= vetting.snr_min and >= 2 epochs with data.
    """
    bench = pd.read_csv(bench_path(root, sector))
    con = connect(root)
    sigs = con.execute(
        "SELECT tic_id, period_days, t0_btjd, sde, snr, iteration FROM signals WHERE run_id = ?",
        [run_id],
    ).df()
    searched = {
        r[0]
        for r in con.execute(
            "SELECT tic_id FROM search_done WHERE run_id = ? AND status = 'ok'", [run_id]
        ).fetchall()
    }
    con.close()
    rank = {"recovered": 3, "recovered_alias": 2, "period_only": 1, "missed": 0}
    rows = []
    for _, toi in bench.iterrows():
        status, best_sde, got_period = "missed", math.nan, math.nan
        snr_exp, n_ep = math.nan, 0
        if toi["tic_id"] not in searched:
            status = "no_data"
        else:
            snr_exp, n_ep = expected_snr(root, cfg, sector, toi)
            for _, s in sigs[sigs["tic_id"] == toi["tic_id"]].iterrows():
                m = match_period(
                    s["period_days"],
                    s["t0_btjd"],
                    toi["period_days"],
                    toi["t0_btjd"],
                    rel_tol=cfg.crossmatch.period_rel_tol,
                    phase_tol=cfg.crossmatch.phase_tol,
                )
                if m is None:
                    continue
                phase_ok = m.phase_consistent in (True, None)
                if float(m.alias) in RECOVERY_ALIASES:
                    new = "recovered" if phase_ok else "period_only"
                elif any(abs(float(m.alias) - a) < 1e-9 for a in WEAK_ALIASES) and phase_ok:
                    new = "recovered_alias"
                else:
                    continue
                if rank[new] > rank[status]:
                    status, best_sde, got_period = new, s["sde"], s["period_days"]
        rows.append(
            {
                **toi.to_dict(),
                "status": status,
                "sde": best_sde,
                "found_period": got_period,
                "snr_expected": snr_exp,
                "epochs_with_data": n_ep,
                "detectable": bool(snr_exp >= cfg.vetting.snr_min and n_ep >= 2),
            }
        )
    return pd.DataFrame(rows)


def report_markdown(
    res: pd.DataFrame,
    sector: int,
    run_id: str,
    cfg: Config,
    elapsed_s: float | None,
    pipeline_version: str,
) -> str:
    have = res[res["status"] != "no_data"]
    det = have[have["detectable"]]

    def _recall(df: pd.DataFrame, statuses: tuple[str, ...]) -> str:
        k, n = int(df["status"].isin(statuses).sum()), len(df)
        if n == 0:
            return "no data"
        lo, hi = wilson(k, n)
        return f"{k}/{n} = {k / n:.1%} (95 % CI {lo:.1%}–{hi:.1%})"

    lines = [
        f"# Recall benchmark — sector {sector}",
        "",
        f"- Date: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        f"- run_id: `{run_id}`",
        f"- pipeline_version: `{pipeline_version}`",
        f"- params_hash: `{cfg.params_hash()}`",
        f"- TOIs in list: {len(res)}; with SPOC 2-min light curve: {len(have)}; "
        f"detectable in one sector (expected SNR >= {cfg.vetting.snr_min}, >= 2 epochs): "
        f"{len(det)}",
        "",
        "Main metric: recall on detectable TOIs. ExoFOP SNR is multi-sector; TOIs with low",
        "expected SNR in this sector cannot be recovered by any pipeline from this data alone.",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| **Recall, detectable** (period 1, 2, 1/2 + phase) | {_recall(det, ('recovered',))} |",
        f"| Recall, detectable, including alias 3, 1/3, 3/2, 2/3 | "
        f"{_recall(det, ('recovered', 'recovered_alias'))} |",
        f"| Recall, all with data | {_recall(have, ('recovered',))} |",
        f"| Period only (phase failed) | {int((have['status'] == 'period_only').sum())} |",
        f"| Detectable missed | {int((det['status'] == 'missed').sum())} |",
    ]
    if elapsed_s is not None:
        lines.append(f"| Search time | {elapsed_s / 60:.1f} min |")
    lines += [
        "",
        "## By depth",
        "",
        "| Depth (ppm) | Recovered | Total | Recall |",
        "|---|---|---|---|",
    ]
    cut = pd.cut(det["depth_ppm"], DEPTH_BINS, right=False)
    for interval, grp in det.groupby(cut, observed=True):
        kk = int((grp["status"] == "recovered").sum())
        lines.append(
            f"| {interval.left:.0f}–{interval.right:.0f} | {kk} | {len(grp)} | "
            f"{kk / len(grp):.0%} |"
        )
    missed = det[det["status"] != "recovered"].sort_values("snr_expected", ascending=False)
    if len(missed):
        lines += [
            "",
            "## Detectable but not recovered",
            "",
            "| TOI | TIC | P (d) | Depth (ppm) | Exp. SNR | Epochs | Tmag | Status | Found P |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for _, r in missed.iterrows():
            found = f"{r['found_period']:.4f}" if pd.notna(r["found_period"]) else "-"
            lines.append(
                f"| {r['toi']} | {r['tic_id']} | {r['period_days']:.4f} | {r['depth_ppm']:.0f} | "
                f"{r['snr_expected']:.1f} | {r['epochs_with_data']} | {r['tmag']:.2f} | "
                f"{r['status']} | {found} |"
            )
    return "\n".join(lines) + "\n"


def write_report(md: str, sector: int, pipeline_version: str) -> Path:
    d = REPO_ROOT / "docs" / "benchmarks"
    d.mkdir(parents=True, exist_ok=True)
    sha = pipeline_version.split("+")[-1]
    p = d / f"{datetime.now(UTC):%Y-%m-%d}-s{sector:04d}-{sha}.md"
    p.write_text(md, encoding="utf-8")
    return p
