"""Orchestration: registers light curves, runs the search in parallel (per target), runs crossmatch.

No scientific logic here; only sequencing, persistence and logging.
Network-free batch path: reads Parquet and local mirrors.
"""

from __future__ import annotations

import json
import math
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from planethunter import __version__
from planethunter.catalogs.mirrors import load_known
from planethunter.config import REPO_ROOT, Config, limit_native_threads, max_workers
from planethunter.crossmatch.core import MatchClass
from planethunter.db.store import connect, insert_df, upsert_df
from planethunter.ingest.lightcurves import META_KEY, LightCurveMeta, read_parquet
from planethunter.log import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------- file discovery and registration


def discover(
    root: Path, *, sector: int | None = None, tic_ids: set[int] | None = None, author: str = "SPOC"
) -> dict[int, list[Path]]:
    """Map tic_id -> Parquet files. Without a sector: all sectors of the target."""
    pattern = f"sector={sector:04d}" if sector is not None else "sector=*"
    out: dict[int, list[Path]] = {}
    for p in (root / "parquet").glob(f"{pattern}/author={author}/tic_*.parquet"):
        tic = int(p.stem.split("_")[1])
        if tic_ids is None or tic in tic_ids:
            out.setdefault(tic, []).append(p)
    return {k: sorted(v) for k, v in sorted(out.items())}


def read_meta(path: Path) -> LightCurveMeta:
    return LightCurveMeta.from_json(pq.read_schema(path).metadata[META_KEY])


def register_lightcurves(root: Path, paths: list[Path]) -> int:
    """Write `targets` and `lightcurves` from the Parquet metadata (cheap: schema only)."""
    metas = [(read_meta(p), p) for p in paths]
    if not metas:
        return 0
    lcs = pd.DataFrame(
        [
            {
                "tic_id": m.tic_id,
                "sector": m.sector,
                "author": m.author,
                "camera": m.camera,
                "ccd": m.ccd,
                "procver": m.procver,
                "data_release": m.data_release,
                "source_file": m.source_file,
                "sha256": m.sha256,
                "n_points": m.n_points,
                "path": str(p.relative_to(root)),
            }
            for m, p in metas
        ]
    )
    stars = pd.DataFrame(
        [{**m.star.to_dict(), "mass_msun": m.star.mass_or_estimate()} for m, _ in metas]
    ).drop_duplicates("tic_id", keep="last")
    con = connect(root)
    try:
        upsert_df(con, "lightcurves", lcs)
        upsert_df(con, "targets", stars)
    finally:
        con.close()
    return len(lcs)


# ---------------------------------------------------------------- search


def pipeline_version() -> str:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        return f"{__version__}+{sha}{'.dirty' if dirty else ''}"
    except Exception:
        return f"{__version__}+nogit"


def _null_kwargs(cfg: Config) -> dict:
    """Parameters of preprocess.apply_null, shared by the search and the vetting of null runs
    (the same tic_id/sector/seed always gives the same transformed light curve)."""
    return dict(
        seed=cfg.search.null_seed,
        gap_days=cfg.search.segment_gap_days,
        cut_days=max(cfg.preprocess.break_tolerance_days, cfg.search.segment_gap_days) + 0.05,
    )


def _null_mode_of(mode: str | None) -> str | None:
    """search_runs.mode -> null transform name ("null-inverted" -> "inverted"), else None."""
    return mode.removeprefix("null-") if mode and mode.startswith("null-") else None


def _process_target(tic_id: int, paths: list[str], cfg_json: str, run_meta: dict) -> dict:
    """Run in a child process: read Parquet, preprocess, TLS. Never raises."""
    t0 = time.perf_counter()
    try:
        from planethunter.preprocess import apply_null
        from planethunter.search import search_target, signal_row

        cfg = Config.model_validate_json(cfg_json)
        frames, star, author = [], None, "SPOC"
        for p in paths:
            df, meta = read_parquet(Path(p))
            frames.append((df, meta.sector))
            star, author = meta.star, meta.author
        # Null runs (Thompson et al. 2018): inverted or scrambled light curves, same search.
        frames = apply_null(frames, run_meta.get("null_mode"), tic_id=tic_id, **_null_kwargs(cfg))
        n_good = sum(int(df["flux"].notna().sum()) for df, _ in frames)
        if n_good < cfg.preprocess.min_points:
            return {
                "tic_id": tic_id,
                "status": "too_few_points",
                "signals": [],
                "elapsed_s": time.perf_counter() - t0,
                "error": None,
            }
        sigs = search_target(frames, star, cfg, tic_id=tic_id, author=author)
        rows = []
        for s in sigs:
            s.run_id, s.pipeline_version, s.params_hash = (
                run_meta["run_id"],
                run_meta["pipeline_version"],
                run_meta["params_hash"],
            )
            rows.append(signal_row(s))
        return {
            "tic_id": tic_id,
            "status": "ok",
            "signals": rows,
            "elapsed_s": time.perf_counter() - t0,
            "error": None,
        }
    except Exception as exc:
        return {
            "tic_id": tic_id,
            "status": "error",
            "signals": [],
            "elapsed_s": time.perf_counter() - t0,
            "error": f"{type(exc).__name__}: {exc}",
        }


@dataclass
class RunSummary:
    run_id: str
    n_targets: int
    n_done: int
    n_signals: int
    n_errors: int
    elapsed_s: float


def run_search(
    root: Path,
    cfg: Config,
    *,
    sector: int | None = None,
    tic_ids: set[int] | None = None,
    all_sectors: bool = False,
    workers: int | None = None,
    resume_run_id: str | None = None,
    batch_size: int = 100,
    null_mode: str | None = None,
) -> RunSummary:
    """Search all selected targets. `all_sectors`: combine all sectors of each target.

    Resumable: with `resume_run_id`, skips targets already processed in that run.
    null_mode: "inverted" | "scrambled" runs the same search on null light curves for the
    empirical false-alarm rate (Thompson et al. 2018); search_runs.mode = "null-<mode>" and
    the run_id carries it. Signals are stored like any other run (provenance kept).
    """
    from planethunter.preprocess import NULL_MODES

    if sector is None and not tic_ids:
        raise ValueError("provide sector or tic_ids")
    if null_mode is not None and null_mode not in NULL_MODES:
        raise ValueError(f"null_mode must be one of {NULL_MODES}")
    if all_sectors:
        seed = discover(root, sector=sector, tic_ids=tic_ids)
        targets = discover(root, tic_ids=set(seed))
    else:
        targets = discover(root, sector=sector, tic_ids=tic_ids)
    register_lightcurves(root, [p for ps in targets.values() for p in ps])

    con = connect(root)
    mode = "multi" if all_sectors else "single"
    run_tag = f"{mode}-null-{null_mode}" if null_mode else mode
    if null_mode:
        mode = f"null-{null_mode}"
    if resume_run_id:
        run_id = resume_run_id
        prev = con.execute("SELECT mode FROM search_runs WHERE run_id = ?", [run_id]).fetchone()
        null_mode = _null_mode_of(str(prev[0])) if prev else null_mode
        done = {
            r[0]
            for r in con.execute(
                "SELECT tic_id FROM search_done WHERE run_id = ?", [run_id]
            ).fetchall()
        }
    else:
        run_id = (
            f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{run_tag}-s{sector if sector is not None else 'x'}"
        )
        done = set()
    run_meta = {
        "run_id": run_id,
        "pipeline_version": pipeline_version(),
        "params_hash": cfg.params_hash(),
        "null_mode": null_mode,
    }
    todo = {k: v for k, v in targets.items() if k not in done}
    if not resume_run_id:
        insert_df(
            con,
            "search_runs",
            pd.DataFrame(
                [
                    {
                        "run_id": run_id,
                        "mode": mode,
                        "sector": sector,
                        "author": "SPOC",
                        "pipeline_version": run_meta["pipeline_version"],
                        "params_hash": run_meta["params_hash"],
                        "params_json": cfg.model_dump_json(),
                        "n_targets": len(targets),
                        "n_done": 0,
                        "n_signals": 0,
                        "n_errors": 0,
                        "started_at": datetime.now(UTC).replace(tzinfo=None),
                        "finished_at": None,
                    }
                ]
            ),
        )
    log.info("search started", extra={"run_id": run_id, "sector": sector, "n": len(todo)})

    n_workers = max_workers(workers, cfg.search.n_workers())
    limit_native_threads()
    cfg_json = cfg.model_dump_json()
    t_start = time.perf_counter()
    sig_buf: list[dict] = []
    done_buf: list[dict] = []
    n_sig = n_err = n_done = 0

    def _flush() -> None:
        if sig_buf:
            insert_df(con, "signals", pd.DataFrame(sig_buf))
            sig_buf.clear()
        if done_buf:
            upsert_df(con, "search_done", pd.DataFrame(done_buf))
            done_buf.clear()

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futs = [
            pool.submit(_process_target, tic, [str(p) for p in ps], cfg_json, run_meta)
            for tic, ps in todo.items()
        ]
        for fut in as_completed(futs):
            res = fut.result()
            n_done += 1
            sig_buf.extend(res["signals"])
            n_sig += len(res["signals"])
            if res["status"] == "error":
                n_err += 1
                log.warning(
                    "search failed",
                    extra={"run_id": run_id, "tic_id": res["tic_id"], "error": res["error"]},
                )
            done_buf.append(
                {
                    "run_id": run_id,
                    "tic_id": res["tic_id"],
                    "status": res["status"],
                    "n_signals": len(res["signals"]),
                    "elapsed_s": res["elapsed_s"],
                    "error": res["error"],
                }
            )
            if len(done_buf) >= batch_size:
                _flush()
                log.info("search progress", extra={"run_id": run_id, "n": n_done})
    _flush()

    totals = con.execute(
        "SELECT count(*), sum(n_signals), sum(CASE WHEN status='error' THEN 1 ELSE 0 END) "
        "FROM search_done WHERE run_id = ?",
        [run_id],
    ).fetchone()
    con.execute(
        "UPDATE search_runs SET n_done=?, n_signals=?, n_errors=?, finished_at=? WHERE run_id=?",
        [
            totals[0],
            int(totals[1] or 0),
            int(totals[2] or 0),
            datetime.now(UTC).replace(tzinfo=None),
            run_id,
        ],
    )
    con.close()
    elapsed = time.perf_counter() - t_start
    log.info(
        "search finished", extra={"run_id": run_id, "n": n_done, "elapsed_s": round(elapsed, 1)}
    )
    return RunSummary(
        run_id, len(targets), int(totals[0]), int(totals[1] or 0), int(totals[2] or 0), elapsed
    )


# ---------------------------------------------------------------- crossmatch


def crossmatch_frame(
    sigs: pd.DataFrame,
    known: pd.DataFrame,
    ages: dict,
    cfg: Config,
    *,
    checked_at: datetime | None = None,
) -> pd.DataFrame:
    """Crossmatch rows for a run's signals (pure; no network, no database).

    Per-signal classification (crossmatch.batch) + run-level flags (crossmatch.runlevel:
    epoch spikes, shared signals). checked_at is naive UTC.
    """
    from planethunter.crossmatch.batch import classify_frame
    from planethunter.crossmatch.runlevel import run_level_flags

    out = classify_frame(sigs, known, ages, cfg.crossmatch)
    if out.empty:
        return out
    flags = run_level_flags(sigs, cfg.crossmatch)
    out = out.merge(flags, on="signal_id", how="left")
    note = out.pop("shared_signal_note")
    has = note.notna() & (note.astype(str) != "")
    out.loc[has, "notes"] = [
        (f"{n} | {x}" if n else str(x))
        for n, x in zip(out.loc[has, "notes"], note[has], strict=True)
    ]
    out["mirror_ages_json"] = json.dumps({getattr(k, "value", k): v for k, v in ages.items()})
    out["checked_at"] = (checked_at or datetime.now(UTC)).astimezone(UTC).replace(tzinfo=None)
    return out


CROSSMATCH_SIGNALS_SQL = (
    "SELECT s.signal_id, s.tic_id, s.period_days, s.period_err_days, s.t0_btjd, "
    "s.duration_hours, s.depth_ppm, s.n_transits, s.transit_times_json, t.ra_deg, t.dec_deg, "
    "t.pmra_mas_yr, t.pmdec_mas_yr, t.tmag "
    "FROM signals s LEFT JOIN targets t USING (tic_id)"
)


def run_crossmatch(root: Path, cfg: Config, run_id: str) -> pd.DataFrame:
    """Classify all signals of a run against the local mirrors. No network.

    Also computes the run-level flags (epoch spikes, shared signals), stores checked_at in
    UTC and records the provenance of the mirrors used in `catalog_mirrors`.
    """
    from planethunter.catalogs.mirrors import mirror_manifest, record_catalog_mirrors

    con = connect(root)
    sigs = con.execute(CROSSMATCH_SIGNALS_SQL + " WHERE s.run_id = ?", [run_id]).df()
    known, ages = load_known(root)
    out = crossmatch_frame(sigs, known, ages, cfg)
    if len(out):
        upsert_df(con, "crossmatch", out)
    record_catalog_mirrors(con, mirror_manifest(root), cfg.crossmatch)
    con.close()
    return out


def candidates(root: Path, cfg: Config, run_id: str) -> pd.DataFrame:
    """Signals of the run that pass the detection cut and are not known."""
    con = connect(root)
    df = con.execute(
        """
        SELECT s.signal_id, s.tic_id, t.tmag, s.sectors, s.period_days, s.t0_btjd,
               s.depth_ppm, s.duration_hours, s.sde, s.snr, s.n_transits,
               s.odd_even_mismatch_sigma, s.edge_transit_fraction,
               c.match_class, c.host_known, c.matched_name, c.notes
        FROM signals s
        JOIN crossmatch c USING (signal_id)
        LEFT JOIN targets t USING (tic_id)
        WHERE s.run_id = ? AND s.sde >= ? AND s.snr >= ? AND s.n_transits >= ?
              AND s.edge_transit_fraction <= ?
              AND c.match_class IN (?, ?)
        ORDER BY s.sde DESC
        """,
        [
            run_id,
            cfg.vetting.sde_min,
            cfg.vetting.snr_min,
            cfg.vetting.min_transits,
            cfg.vetting.max_edge_transit_fraction,
            MatchClass.NEW.value,
            MatchClass.UNVERIFIED.value,
        ],
    ).df()
    con.close()
    return df


# ---------------------------------------------------------------- vetting


def _vet_target(
    tic_id: int,
    paths: list[str],
    sig_rows: list[dict],
    cfg_json: str,
    null_mode: str | None = None,
) -> dict:
    """Child process: redo the detrending with each signal's window and run basic vetting.

    null_mode ("inverted" | "scrambled", from search_runs.mode): signals of a null run are
    vetted on the same transformed light curve the search saw.
    """
    try:
        from planethunter.preprocess import apply_null, flatten_for_signal, signal_windows
        from planethunter.vetting import VetSignal, vet_signal

        cfg = Config.model_validate_json(cfg_json)
        frames, star = [], None
        for p in paths:
            df, meta = read_parquet(Path(p))
            frames.append((df, meta.sector))
            star = meta.star
        frames = apply_null(frames, null_mode, tic_id=tic_id, **_null_kwargs(cfg))
        # `sector` lets the MOM_CENTR centroid test work per sector (CCD frames differ).
        raw = pd.concat([df.assign(sector=s) for df, s in frames], ignore_index=True).sort_values(
            "time"
        )
        out = []
        for row in sig_rows:
            if not row.get("_gated", True):
                continue  # below the cut: only used as a mask for the others
            # Each sector with ITS search-time window (never < 3 x T14), the signal's transits
            # masked so the trend is interpolated across them (Hippke et al. 2019).
            windows = signal_windows(
                row.get("detrend_windows_json"),
                row.get("detrend_window_days"),
                row["duration_hours"] / 24,
                [s for _, s in frames],
                cfg.preprocess,
            )
            flat = flatten_for_signal(
                frames,
                cfg.preprocess,
                windows=windows,
                period_days=row["period_days"],
                t0_btjd=row["t0_btjd"],
                duration_days=row["duration_hours"] / 24,
            )
            # Stronger signals mask this one and feed the independence test. Weaker ones are
            # masked only if vetting.mask_weaker_signals (audit G7; off: an EB's own eclipses
            # are often re-detected at non-alias periods).
            sib = [o for o in sig_rows if o["signal_id"] != row["signal_id"]]
            others = [
                (o["period_days"], o["t0_btjd"], o["duration_hours"] / 24)
                for o in sib
                if o["sde"] > row["sde"]
            ]
            weaker = [
                (o["period_days"], o["t0_btjd"], o["duration_hours"] / 24)
                for o in sib
                if o["sde"] <= row["sde"] and cfg.vetting.mask_weaker_signals
            ]
            sig = VetSignal(
                period_days=row["period_days"],
                t0_btjd=row["t0_btjd"],
                duration_days=row["duration_hours"] / 24,
                depth_ppm=row["depth_ppm"],
                sde=row["sde"],
                snr=row["snr"],
                n_transits=int(row["n_transits"]),
                edge_transit_fraction=float(row["edge_transit_fraction"] or 0.0),
                snr_pink=_opt(row.get("snr_pink")),
            )
            rep = vet_signal(
                sig, flat, raw, star, cfg.vetting, other_signals=others, weaker_signals=weaker
            )
            out.append(
                {
                    "signal_id": int(row["signal_id"]),
                    "level": "basic",
                    "score": rep.score,
                    "verdict": rep.verdict,
                    "vetoed_by": ",".join(rep.vetoed_by),
                    "failed": ",".join(rep.failed),
                    "deep_pending": ",".join(rep.deep_pending),
                    "fit_depth_ppm": rep.fit.get("depth_ppm"),
                    "fit_t14_hours": rep.fit.get("t14_hours"),
                    "fit_tau_frac": rep.fit.get("tau_frac"),
                    "fit_rp_rs": rep.fit.get("rp_rs"),
                    "tests_json": json.dumps(rep.to_rows(), default=float, ensure_ascii=False),
                    "params_hash": cfg.params_hash(),
                }
            )
        return {"tic_id": tic_id, "rows": out, "error": None}
    except Exception as exc:
        return {"tic_id": tic_id, "rows": [], "error": f"{type(exc).__name__}: {exc}"}


def _optional_columns(con, table: str, cols: tuple[str, ...], alias: str = "") -> str:
    """SELECT list for columns that may be missing in an unmigrated (read-only) database."""
    have = {
        r[0]
        for r in con.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?", [table]
        ).fetchall()
    }
    pre = f"{alias}." if alias else ""
    return ", ".join(f"{pre}{c}" if c in have else f"NULL AS {c}" for c in cols)


def run_vetting(
    root: Path, cfg: Config, run_id: str, *, workers: int | None = None, write: bool = True
) -> pd.DataFrame:
    """Basic vetting of all signals of the run with SDE >= vetting.sde_min. No network.

    write=False only computes (used to build training data without contending for the DB).
    """
    con = connect(root, read_only=not write)
    # A read-only connection does not migrate: columns added later (snr_pink,
    # detrend_windows_json) are read as NULL from an older database.
    sel = _optional_columns(con, "signals", ("snr_pink", "detrend_windows_json"))
    sigs = con.execute(
        "SELECT signal_id, tic_id, period_days, t0_btjd, duration_hours, depth_ppm, sde, snr, "
        f"n_transits, edge_transit_fraction, detrend_window_days, sectors, {sel} "
        "FROM signals WHERE run_id = ?",
        [run_id],
    ).df()
    run_mode = con.execute("SELECT mode FROM search_runs WHERE run_id = ?", [run_id]).fetchone()
    con.close()
    null_mode = _null_mode_of(str(run_mode[0])) if run_mode else None
    if sigs.empty:
        return pd.DataFrame()
    sigs = sigs.replace({np.nan: None})
    todo = sigs[sigs["sde"] >= cfg.vetting.sde_min]
    cfg_json = cfg.model_dump_json()
    rows, errors = [], []
    limit_native_threads()
    with ProcessPoolExecutor(max_workers=max_workers(workers, cfg.search.n_workers())) as pool:
        futs = []
        for tic, grp in todo.groupby("tic_id"):
            sectors = {int(s) for s in str(grp["sectors"].iloc[0]).split(",") if s}
            paths = [
                str(p)
                for p in discover(root, tic_ids={int(tic)}).get(int(tic), [])
                if int(p.parent.parent.name.split("=")[1]) in sectors
            ]
            # Other signals of the target (even below the cut) are included for masking.
            all_rows = sigs[sigs["tic_id"] == tic].to_dict("records")
            gated = set(grp["signal_id"])
            futs.append(
                pool.submit(
                    _vet_target,
                    int(tic),
                    paths,
                    [r | {"_gated": r["signal_id"] in gated} for r in all_rows],
                    cfg_json,
                    null_mode,
                )
            )
        for fut in as_completed(futs):
            res = fut.result()
            if res["error"]:
                errors.append(res)
                log.warning(
                    "vetting failed", extra={"tic_id": res["tic_id"], "error": res["error"]}
                )
            rows += res["rows"]
    out = pd.DataFrame(rows)
    out = out[out["signal_id"].isin(set(todo["signal_id"]))] if len(out) else out
    if len(out):
        out = out.assign(**_ml_columns(root, cfg, out["tests_json"]))
    if not write:
        return out
    con = connect(root)
    upsert_df(con, "vetting", out)
    con.close()
    log.info("vetting finished", extra={"run_id": run_id, "n": len(out), "error": len(errors)})
    return out


CANDIDATE_COLUMNS = [
    "signal_id",
    "tic_id",
    "run_id",
    "match_class",
    "verdict",
    "score",
    "severity",
    "review_status",
    "review_note",
    "reviewed_at",
    "dossier_path",
]
R_EARTH_PER_R_SUN = 109.076


def _ml_columns(root: Path, cfg: Config, tests_json) -> dict:
    """p_planet (= p_rank), p_abs and model_version from the current model (None if no model)."""
    from planethunter.ml.calibrate import load_model, model_version, p_abs, predict

    model = load_model(root)
    if not model:
        return {"p_planet": None, "p_abs": None, "model_version": None}
    p = [predict(model, json.loads(t or "[]")) for t in tests_json]
    return {
        "p_planet": p,
        "p_abs": [p_abs(model, x, cfg.severity.new_prior) for x in p],
        "model_version": model_version(model),
    }


def _deep_done(tests: list[dict], deep_pending: str | None) -> bool:
    """Deep vetting complete (audit A3): TPF difference image, Gaia neighbors and FPP all
    returned a result AND passed. A test with no result (None) does not count as done."""
    by = {t["name"]: t for t in tests}

    def ok(name: str) -> bool:
        t = by.get(name) or {}
        return t.get("passed") is True and not t.get("veto")

    return (
        ok("tpf_difference_image")
        and ok("gaia_neighbors")
        and ok("fpp_triceratops")
        and "fpp_triceratops" not in str(deep_pending or "")
    )


def _outside_validation_region(tests: list[dict]) -> bool:
    """Validation-region flag written by deep vetting into the fpp_triceratops test:
    `extra.in_validation_region` (bool), else a `validation_region` field, else the phrase
    "outside (the) validation region" in its note. Absent = no flag (severity still checks Rp,
    SNR and cadence itself)."""
    t = next((t for t in tests if t.get("name") == "fpp_triceratops"), None)
    if t is None:
        return False
    extra = t.get("extra") or {}
    if isinstance(extra, dict) and extra.get("in_validation_region") is not None:
        return not bool(extra["in_validation_region"])
    if t.get("validation_region") is not None:
        return not bool(t["validation_region"])
    note = str(t.get("note") or "").lower().replace("_", " ")
    return "outside validation region" in note or "outside the validation region" in note


def _rp_rearth(depth_ppm, rp_rs, radius_rsun) -> float | None:
    """Planet radius (R_earth) from the larger of sqrt(depth) and the fitted Rp/R*; None
    without a stellar radius. Conservative for the Rp < 8 R_earth cut of P0."""
    if radius_rsun is None or pd.isna(radius_rsun):
        return None
    ks = []
    if depth_ppm is not None and pd.notna(depth_ppm) and depth_ppm > 0:
        ks.append(math.sqrt(float(depth_ppm) * 1e-6))
    if rp_rs is not None and pd.notna(rp_rs) and rp_rs > 0:
        ks.append(float(rp_rs))
    return max(ks) * float(radius_rsun) * R_EARTH_PER_R_SUN if ks else None


def _two_min(author, cfg: Config) -> bool:
    parts = [a.strip() for a in str(author or "").split(",") if a.strip()]
    return bool(parts) and all(a in cfg.severity.two_min_authors for a in parts)


def _opt(x) -> float | None:
    return None if x is None or pd.isna(x) else float(x)


def promote_candidates(root: Path, cfg: Config, run_id: str) -> pd.DataFrame:
    """Join signals + crossmatch + vetting and write `candidates`. Preserves human review.

    p_rank comes from the current model: rows vetted with another model version (or none) are
    rescored from tests_json and vetting.p_planet/p_abs/model_version updated. The model's
    operating points (P1/P2 cuts) feed the severity rules (alerts/severity.py).
    """
    from planethunter.alerts.severity import PARTIAL_TRANSIT_TOKEN, PERIODLESS_TOKEN, severity
    from planethunter.ml.calibrate import load_model, model_cuts, model_version

    con = connect(root)
    df = con.execute(
        """
        SELECT s.signal_id, s.tic_id, s.run_id, s.snr AS sig_snr, s.author,
               c.match_class, c.host_eb, c.notes AS xm_notes, c.epoch_spike_frac,
               c.shared_signal_role, v.verdict, v.score, v.deep_pending, v.fpp, v.nfpp,
               v.p_planet, v.model_version, v.fit_depth_ppm, v.fit_rp_rs, v.tests_json,
               t.radius_rsun, k.review_status, k.review_note, k.reviewed_at, k.dossier_path
        FROM signals s
        JOIN crossmatch c USING (signal_id)
        JOIN vetting v USING (signal_id)
        LEFT JOIN candidates k USING (signal_id)
        LEFT JOIN targets t ON t.tic_id = s.tic_id
        WHERE s.run_id = ?
        """,
        [run_id],
    ).df()
    if df.empty:
        con.close()
        return df
    model = load_model(root)
    mv = model_version(model)
    if model is None:
        df["p_planet"] = None  # no model, no ML: deterministic rules only
    else:
        stale = (df["model_version"].fillna("") != mv).to_numpy()
        if stale.any():
            upd = pd.DataFrame(
                {"signal_id": df.loc[stale, "signal_id"].to_numpy()}
                | _ml_columns(root, cfg, df.loc[stale, "tests_json"])
            )
            df.loc[stale, "p_planet"] = upd["p_planet"].to_numpy()
            con.register("_ml_upd", upd)
            try:
                con.execute(
                    "UPDATE vetting SET p_planet = u.p_planet, p_abs = u.p_abs, "
                    "model_version = u.model_version FROM _ml_upd u "
                    "WHERE vetting.signal_id = u.signal_id"
                )
            finally:
                con.unregister("_ml_upd")
    cuts = model_cuts(model, cfg.severity.p1_cut_fallback, cfg.severity.p2_cut_fallback)
    spike_max = getattr(cfg.crossmatch, "epoch_spike_max_frac", None)
    sev = []
    for r in df.itertuples():
        tests = json.loads(r.tests_json or "[]")
        sev.append(
            severity(
                r.match_class,
                r.verdict,
                _opt(r.score),
                deep_done=_deep_done(tests, r.deep_pending),
                fpp=_opt(r.fpp),
                nfpp=_opt(r.nfpp),
                host_eb=bool(r.host_eb) if pd.notna(r.host_eb) else False,
                star_known=pd.notna(r.radius_rsun),
                p_planet=_p_final(r.p_planet, r.tests_json, cfg),
                p1_cut=cuts["p1_cut"],
                p2_cut=cuts["p2_cut"],
                rp_rearth=_rp_rearth(r.fit_depth_ppm, r.fit_rp_rs, r.radius_rsun),
                snr=_opt(r.sig_snr),
                two_min_cadence=_two_min(r.author, cfg),
                outside_validation_region=_outside_validation_region(tests),
                epoch_spike_frac=_opt(r.epoch_spike_frac),
                epoch_spike_max_frac=spike_max,
                shared_signal_role=r.shared_signal_role if pd.notna(r.shared_signal_role) else None,
                periodless_known_on_host=PERIODLESS_TOKEN in str(r.xm_notes or ""),
                partial_known_transit=PARTIAL_TRANSIT_TOKEN in str(r.xm_notes or ""),
                cfg=cfg.severity,
            )
        )
    df["severity"] = sev
    df["review_status"] = df["review_status"].fillna("pending")
    out = df.loc[df["severity"] != "NONE", CANDIDATE_COLUMNS]
    if len(out):
        upsert_df(con, "candidates", out)
    # Anything that dropped to NONE (e.g. failed deep vetting) leaves the queue, unless already
    # reviewed by a human. Previously, the failed signal 1528 stayed listed as P2.
    dropped = [int(x) for x in df.loc[df["severity"] == "NONE", "signal_id"]]
    if dropped:
        con.execute(
            "DELETE FROM candidates WHERE review_status = 'pending' AND signal_id IN "
            f"({','.join(str(x) for x in dropped)})"
        )
    con.close()
    return out


DEEP_TEST_NAMES = (
    "tpf_difference_image",
    "gaia_neighbors",
    "gaia_eb",
    "simbad_type",
    "other_sectors",
    "fpp_triceratops",
)


def _p_final(p_planet: float | None, tests_json: str | None, cfg: Config) -> float | None:
    """p_rank (basic vetting) adjusted by deep vetting, in odds space.

    The model does not see the deep tests (they do not exist for the known objects used in
    training), hence this explicit adjustment. Each failed deep test multiplies the odds by its
    weight read as a likelihood ratio LR = P(fail | planet) / P(fail | false positive), capped
    at 1: logit(p_final) = logit(p_rank) + sum(ln LR). The weights are a heuristic rank
    penalty (hand-set in vetting.weights, not measured). A veto gives 0. The result never
    exceeds p_rank.
    """
    if p_planet is None or (isinstance(p_planet, float) and math.isnan(p_planet)):
        return None
    p = float(p_planet)
    log_lr = 0.0
    for t in json.loads(tests_json or "[]"):
        if t["name"] not in DEEP_TEST_NAMES:
            continue
        if t.get("veto"):
            return 0.0
        if t.get("passed") is False:
            w = min(1.0, max(1e-6, float(cfg.vetting.weights.get(t["name"], 0.5))))
            log_lr += math.log(w)
    if log_lr == 0.0:
        return p
    q = min(max(p, 1e-12), 1 - 1e-12)
    z = math.log(q / (1 - q)) + log_lr
    return min(p, 1.0 / (1.0 + math.exp(-z)))


def candidate_table(
    root: Path, run_id: str | None = None, *, include_rejected: bool = False
) -> pd.DataFrame:
    """Candidates with the essentials for review, by severity and score.

    p_rank = ML ranking probability (training prior; what severity uses through the model's
    cuts); p_abs = prior-corrected display value (severity.new_prior, an assumption).
    Systematics flags come from the crossmatch (NULL for runs before 2026-10-10).
    """
    con = connect(root)
    conds, params = [], []
    if run_id:
        conds.append("k.run_id = ?")
        params.append(run_id)
    if not include_rejected:
        conds.append("k.review_status <> 'rejected'")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    df = con.execute(
        f"""
        SELECT k.severity, k.signal_id, k.tic_id, t.tmag, s.sectors,
               round(s.period_days, 5) AS period_d, round(v.fit_depth_ppm) AS depth_ppm,
               round(v.fit_t14_hours, 2) AS t14_h,
               round(sqrt(greatest(v.fit_depth_ppm, 0) * 1e-6) * t.radius_rsun * 109.076, 2)
                   AS rp_rearth,
               round(s.sde, 1) AS sde, round(s.snr, 1) AS snr, s.n_transits,
               round(k.score, 2) AS score, round(v.p_planet, 3) AS p_rank,
               round(v.p_abs, 3) AS p_abs, v.failed,
               round(c.epoch_spike_frac, 2) AS epoch_spike_frac, c.shared_signal_role,
               c.shared_signal_tic,
               coalesce(contains(c.notes, 'periodless_known_on_host'), false)
                   AS periodless_known_on_host,
               c.host_known, k.review_status
        FROM candidates k
        JOIN signals s USING (signal_id)
        JOIN vetting v USING (signal_id)
        JOIN crossmatch c USING (signal_id)
        LEFT JOIN targets t ON t.tic_id = k.tic_id
        {where}
        ORDER BY k.severity, k.score DESC, v.p_planet DESC NULLS LAST, s.sde DESC
        """,
        params,
    ).df()
    con.close()
    return df


def vetting_validation(root: Path, run_id: str) -> pd.DataFrame:
    """Vetting pass rate per crossmatch class: the run itself as a benchmark.

    Expected: KNOWN_PLANET almost all PASS; KNOWN_FP almost all FAIL.
    """
    con = connect(root)
    df = con.execute(
        """
        SELECT c.match_class, v.verdict, v.vetoed_by, v.failed
        FROM vetting v JOIN signals s USING (signal_id) JOIN crossmatch c USING (signal_id)
        WHERE s.run_id = ?
        """,
        [run_id],
    ).df()
    con.close()
    rows = []
    for cls, grp in df.groupby("match_class"):
        fails = grp["failed"].fillna("").str.split(",").explode()
        vetoes = grp["vetoed_by"].fillna("").str.split(",").explode()
        rows.append(
            {
                "class": cls,
                "n": len(grp),
                "pass": int((grp["verdict"] == "PASS_BASIC").sum()),
                "pass_rate": round(float((grp["verdict"] == "PASS_BASIC").mean()), 2),
                "common_failures": fails[fails != ""].value_counts().head(4).to_dict(),
                "vetoes": vetoes[vetoes != ""].value_counts().head(3).to_dict(),
            }
        )
    return pd.DataFrame(rows)


def _deep_one(root_s: str, cfg_json: str, row: dict, max_sectors: int) -> dict:
    """Deep vetting of ONE candidate. Runs in a child process; does not touch the DB.

    Returns the row to write to `vetting`, or {"signal_id", "error"} if it fails entirely.
    """
    from types import SimpleNamespace

    from planethunter.ingest.lightcurves import parse_lc_filename
    from planethunter.ingest.mast import ingest_target, target_lc_urls
    from planethunter.preprocess import flatten_for_signal, signal_windows
    from planethunter.vetting.basic import TestResult, _score
    from planethunter.vetting.deep import (
        PIXEL_ARCSEC,
        difference_image_test,
        fetch_gaia_eb,
        fetch_gaia_neighbors,
        fetch_pixels,
        fetch_simbad_type,
        fpp_test,
        gaia_eb_test,
        neighbor_pixels,
        neighbors_test,
        other_sectors_test,
        sector_presence,
        simbad_test,
    )

    root = Path(root_s)
    cfg = Config.model_validate_json(cfg_json)
    r = SimpleNamespace(**row)

    def _num(x) -> float | None:
        return None if x is None or pd.isna(x) else float(x)

    try:
        basic = [
            TestResult(**d)
            for d in json.loads(r.tests_json)
            if d["name"]
            not in (
                "fpp_triceratops",
                "tpf_difference_image",
                "gaia_neighbors",
                "other_sectors",
                "simbad_type",
                "gaia_eb",
            )
        ]
        vc = cfg.vetting
        by_name = {t.name: t for t in basic}
        # A7: a signal re-vetted at P/2 is deep-vetted at P/2 too.
        period = r.period_days
        if "period_halved" in by_name and by_name["period_halved"].value:
            period = float(by_name["period_halved"].value)
        r.period_days = period
        dur = r.duration_hours / 24
        pm = {"pmra_mas_yr": _num(r.pmra_mas_yr), "pmdec_mas_yr": _num(r.pmdec_mas_yr)}
        diff_results, errs = [], []
        apertures: dict[int, list[list[int]]] = {}
        pixels: dict[int, object] = {}
        for sector in [int(x) for x in str(r.sectors).split(",") if x][:max_sectors]:
            try:
                pix = fetch_pixels(int(r.tic_id), sector, root, r.ra_deg, r.dec_deg, **pm)
                apertures[sector] = pix.aperture_pixels()
                pixels[sector] = pix
                tr, info = difference_image_test(
                    pix,
                    period,
                    r.t0_btjd,
                    dur,
                    max_offset_px=vc.tpf_max_offset_px,
                    nsigma=vc.tpf_offset_sigma,
                )
                diff_results.append(tr)
                if info:
                    _save_diff_png(root, int(r.signal_id), sector, info)
                if tr.extra.get("err_px"):
                    errs.append(float(tr.extra["err_px"]))
            except Exception as exc:
                diff_results.append(
                    TestResult(
                        "tpf_difference_image",
                        None,
                        1.0,
                        None,
                        note=f"sector {sector}: {type(exc).__name__}: {exc}"[:200],
                    )
                )
        known = [d for d in diff_results if d.passed is not None]
        diff = TestResult(
            "tpf_difference_image",
            max((d.value for d in known), default=None),
            vc.tpf_max_offset_px,
            None if not known else all(d.passed for d in known),
            note=" | ".join(d.note for d in diff_results),
            extra={"sectors": [d.extra for d in diff_results if d.extra]},
        )
        excl_px = max(0.3, 3 * min(errs)) if errs else 1.0
        try:
            nb, t_target, gnote = fetch_gaia_neighbors(
                int(r.tic_id), r.ra_deg, r.dec_deg, root, tmag=_num(r.tmag), **pm
            )
            if t_target is None or (nb.empty and gnote):
                gaia = TestResult(
                    "gaia_neighbors", None, 0, None, note=f"error: {gnote or 'no target Tmag'}"
                )
            else:
                # Pixel geometry from the first sector with a TPF (aperture + WCS).
                sec0 = next(iter(pixels), None)
                kw: dict = {}
                if sec0 is not None:
                    pix0 = pixels[sec0]
                    nb = neighbor_pixels(nb, pix0)
                    ex0 = next((d.extra for d in diff_results if d.extra.get("sector") == sec0), {})
                    kw = {
                        "aperture": pix0.aperture,
                        "target_xy": pix0.target_xy,
                        "diff_xy": tuple(ex0["c_diff"]) if ex0.get("c_diff") else None,
                        "diff_offset_significant": bool(ex0.get("offset_significant")),
                        "diff_radius_px": max(vc.tpf_max_offset_px, 3 * (ex0.get("err_px") or 0)),
                    }
                gaia = neighbors_test(
                    nb,
                    t_target,
                    r.fit_depth_ppm,
                    exclusion_radius_arcsec=excl_px * PIXEL_ARCSEC,
                    psf_sigma_px=vc.psf_sigma_px,
                    **kw,
                )
                if gnote:
                    gaia.note += f" ({gnote})"
        except Exception as exc:
            gaia = TestResult(
                "gaia_neighbors", None, 0, None, note=f"{type(exc).__name__}: {exc}"[:200]
            )
        # Other sectors: the signal should reappear (up to 3 sectors, the most recent ones).
        own = {int(x) for x in str(r.sectors).split(",") if x}
        presence: dict[int, dict] = {}
        try:
            avail = sorted(
                {p[0] for u in target_lc_urls(int(r.tic_id)) if (p := parse_lc_filename(u))} - own
            )[-max_sectors:]
            if avail:
                ingest_target(int(r.tic_id), root, sectors=avail)
            for sec in avail:
                path = root / "parquet" / f"sector={sec:04d}" / "author=SPOC"
                path = path / f"tic_{int(r.tic_id):016d}.parquet"
                if path.exists():
                    # Same re-detrend as vetting: window >= 3xT14 and the predicted transits
                    # masked, so a long transit is not eaten before its presence is measured.
                    lc_o = flatten_for_signal(
                        [(read_parquet(path)[0], sec)],
                        cfg.preprocess,
                        windows=signal_windows(None, None, dur, [sec], cfg.preprocess),
                        period_days=float(period),
                        t0_btjd=float(r.t0_btjd),
                        duration_days=float(dur),
                    )
                    presence[sec] = sector_presence(
                        lc_o.time,
                        lc_o.flux.astype(float),
                        period,
                        dur,
                        r.fit_depth_ppm,
                        null_trials=vc.other_sectors_null_trials,
                    )
            blind = None
            blind_error = None
            frames_o = []
            for sec in avail:
                path = root / "parquet" / f"sector={sec:04d}" / "author=SPOC"
                path = path / f"tic_{int(r.tic_id):016d}.parquet"
                if path.exists():
                    frames_o.append((read_parquet(path)[0], sec))
            if frames_o:
                from planethunter.crossmatch.core import match_period
                from planethunter.search import search_target

                star_o = read_meta(path).star if path.exists() else None
                try:
                    found = search_target(frames_o, star_o, cfg, tic_id=int(r.tic_id))
                except ValueError as exc:
                    # TLS 2.0 edge case (2026-10-13): for ultra-short periods over sectors years
                    # apart its detection statistics build an empty in-transit template
                    # ("zero-size array ... minimum"). Keep the per-sector presence result.
                    found = None
                    blind_error = f"blind search failed ({type(exc).__name__}: {exc})"[:160]
            if frames_o and found is not None:
                hits = [
                    s2
                    for s2 in found
                    if s2.sde >= cfg.vetting.sde_min
                    and (
                        m := match_period(
                            s2.period_days, None, r.period_days, None, rel_tol=0.01, phase_tol=1.0
                        )
                    )
                    is not None
                    and float(m.alias) in (1.0, 2.0, 0.5)
                ]
                exp_tot = math.sqrt(
                    sum(
                        x["expected_snr"] ** 2
                        for x in presence.values()
                        if np.isfinite(x["expected_snr"])
                    )
                )
                top = ", ".join(f"{s2.period_days:.3f} d (SDE {s2.sde:.0f})" for s2 in found[:3])
                blind = {
                    "recovered": bool(hits),
                    "expected_total": exp_tot,
                    "note": (
                        f"recovered P = {hits[0].period_days:.4f} d"
                        if hits
                        else f"not recovered; peaks: {top or 'none'}"
                    )
                    + f" (sectors {[sx for _, sx in frames_o]}, expected SNR {exp_tot:.0f})",
                }
            other = other_sectors_test(presence, r.fit_depth_ppm, blind=blind)
            if blind_error:
                other.note = f"{other.note} | {blind_error}" if other.note else blind_error
        except Exception as exc:
            other = TestResult(
                "other_sectors", None, 10.0, None, note=f"{type(exc).__name__}: {exc}"[:200]
            )
        try:
            simb = simbad_test(fetch_simbad_type(r.ra_deg, r.dec_deg), vc.simbad_fail_otypes)
        except Exception as exc:
            simb = TestResult(
                "simbad_type", None, None, None, note=f"{type(exc).__name__}: {exc}"[:200]
            )
        try:
            geb = gaia_eb_test(fetch_gaia_eb(r.ra_deg, r.dec_deg), period)
        except Exception as exc:
            geb = TestResult("gaia_eb", None, None, None, note=f"{type(exc).__name__}: {exc}"[:200])
        fit = {
            "depth": (r.fit_depth_ppm or 0) * 1e-6,
            "t14_days": (r.fit_t14_hours or 0) / 24,
            "tau_frac": r.fit_tau_frac,
            "rp_rs": r.fit_rp_rs,
        }
        tests = [*basic, diff, gaia, other, simb, geb]
        rep = _score(tests, cfg.vetting, fit)
        fpp_res: dict = {}
        # FPP is expensive (~6 min with 1e5 draws): only for candidates that passed everything else.
        if rep.verdict == "PASS_BASIC" and apertures and vc.fpp_enabled:
            fpp_res = _fpp_for(root, cfg, r, apertures, dur)
            # Larger of sqrt(depth) and the limb-darkened k (conservative for Rp < 8 R_earth).
            rp = _rp_rearth(r.fit_depth_ppm, r.fit_rp_rs, _num(r.radius_rsun))
            snr_t = by_name.get("snr")
            snr = float(snr_t.value) if snr_t and snr_t.value is not None else _num(r.snr)
            exp_d = fpp_res.get("exptime_days")
            tests.append(
                fpp_test(
                    fpp_res,
                    rp_rearth=rp,
                    snr=snr,
                    exptime_min=exp_d * 1440 if exp_d else None,
                    candidate_max=vc.fpp_max,
                    nfpp_fail=vc.fpp_nfpp_fail,
                    nfpp_veto=vc.fpp_nfpp_veto,
                    validated_fpp=vc.fpp_validated,
                    validated_nfpp=vc.fpp_nfpp_validated,
                    region_max_rp=vc.fpp_validation_max_rp_rearth,
                    region_min_snr=vc.fpp_validation_min_snr,
                    region_max_exptime_min=vc.fpp_validation_max_exptime_min,
                )
            )
            rep = _score(tests, cfg.vetting, fit)
        return {
            "signal_id": int(r.signal_id),
            "level": "basic+deep",
            "score": rep.score,
            "verdict": rep.verdict,
            "vetoed_by": ",".join(rep.vetoed_by),
            "failed": ",".join(rep.failed),
            "deep_pending": "" if fpp_res.get("ok") else "fpp_triceratops",
            "fpp": fpp_res.get("fpp"),
            "nfpp": fpp_res.get("nfpp"),
            "tests_json": json.dumps(rep.to_rows(), default=float, ensure_ascii=False),
        }
    except Exception as exc:
        return {"signal_id": int(r.signal_id), "error": f"{type(exc).__name__}: {exc}"[:300]}


def _write_deep(root: Path, row: dict) -> None:
    con = connect(root)
    try:
        con.execute(
            """
            UPDATE vetting SET level = ?, score = ?, verdict = ?, vetoed_by = ?, failed = ?,
                   deep_pending = ?, fpp = ?, nfpp = ?, tests_json = ?,
                   vetted_at = current_timestamp
            WHERE signal_id = ?
            """,
            [
                row["level"],
                row["score"],
                row["verdict"],
                row["vetoed_by"],
                row["failed"],
                row["deep_pending"],
                row["fpp"],
                row["nfpp"],
                row["tests_json"],
                row["signal_id"],
            ],
        )
    finally:
        con.close()


def run_deep_vetting(
    root: Path,
    cfg: Config,
    run_id: str | None = None,
    *,
    max_sectors: int = 3,
    workers: int | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Deep vetting (TPF, Gaia, SIMBAD, other sectors, FPP) of the candidates.

    Parallel per candidate (`vetting.deep_workers` processes). Each result is written as soon
    as it is ready, so an interruption does not lose finished work; candidates already at
    level `basic+deep` are skipped unless `force`. Measured in sector 107: sequential took
    ~4-5 min per candidate (62 candidates ~ 4-5 h).
    """
    con = connect(root)
    where, params = ("WHERE k.run_id = ?", [run_id]) if run_id else ("", [])
    win = _optional_columns(con, "signals", ("detrend_windows_json",), alias="s")
    cands = con.execute(
        f"""
        SELECT k.signal_id, s.tic_id, s.sectors, s.period_days, s.t0_btjd, s.duration_hours,
               s.detrend_window_days, {win}, s.snr, v.fit_depth_ppm, v.tests_json, v.fit_t14_hours,
               v.fit_tau_frac, v.fit_rp_rs, v.level, t.ra_deg, t.dec_deg, t.pmra_mas_yr,
               t.pmdec_mas_yr, t.tmag, t.radius_rsun
        FROM candidates k JOIN signals s USING (signal_id) JOIN vetting v USING (signal_id)
        LEFT JOIN targets t ON t.tic_id = s.tic_id
        {where}
        """,
        params,
    ).df()
    con.close()
    if not force:
        cands = cands[cands["level"] != "basic+deep"]
    cands = cands.drop(columns=["level"]).replace({np.nan: None})
    n_workers = max_workers(workers, cfg.vetting.deep_workers)
    limit_native_threads()
    cfg_json = cfg.model_dump_json()
    rows: list[dict] = []
    log.info("deep vetting started", extra={"run_id": run_id, "n": len(cands)})
    with ProcessPoolExecutor(max_workers=max(1, n_workers)) as pool:
        futs = [
            pool.submit(_deep_one, str(root), cfg_json, rec, max_sectors)
            for rec in cands.to_dict("records")
        ]
        for i, fut in enumerate(as_completed(futs), 1):
            row = fut.result()
            if "error" in row:
                log.warning("deep vetting failed", extra={"run_id": run_id, "error": row["error"]})
                continue
            _write_deep(root, row)
            rows.append(row)
            log.info(
                "deep vetting progress",
                extra={"run_id": run_id, "n": i, "stage": f"{i}/{len(futs)}"},
            )
    return pd.DataFrame(rows)


def _save_diff_png(root: Path, signal_id: int, sector: int, info: dict) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, key, title in ((axes[0], "oot", "Out of transit"), (axes[1], "diff", "Difference")):
        ax.imshow(info[key], origin="lower", cmap="viridis")
        ax.contour(info["aperture"], levels=[0.5], colors="w", linewidths=1)
        ax.plot(*info["c_oot"], "w+", ms=12, mew=2, label="out-of-transit centroid")
        ax.plot(*info["c_diff"], "rx", ms=12, mew=2, label="difference centroid")
        if info.get("target_xy") is not None:  # catalog position, propagated with proper motion
            ax.plot(*info["target_xy"], "o", mfc="none", mec="orange", ms=14, mew=2, label="TIC")
        ax.set_title(title)
    axes[1].legend(loc="upper right", fontsize=8)
    dest = root / "cache" / "diffimg" / f"sig{signal_id}_s{sector}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=90, bbox_inches="tight")
    plt.close(fig)
    return dest


def _fpp_for(root: Path, cfg: Config, r, apertures: dict[int, list[list[int]]], dur: float) -> dict:
    """Phase-folded light curve of the candidate (signal window) and isolated triceratops call.

    PDCSAP flux (dilution_corrected=True); exptime = median cadence of the light curve [days].
    The result carries `exptime_days` so fpp_test can flag the 2-min validation region.
    Same re-detrending as basic vetting (`_vet_target`): per-sector search-time windows, never
    below min_window_durations x T14, with the signal's transits masked. `r.period_days` is
    the vetted period (P/2 when basic vetting halved it; set by `_deep_one`).
    """
    from planethunter.preprocess import flatten_for_signal, signal_windows
    from planethunter.vetting.basic import phase_days
    from planethunter.vetting.deep import run_fpp

    frames = []
    for sec in [int(x) for x in str(r.sectors).split(",") if x]:
        p = root / "parquet" / f"sector={sec:04d}" / "author=SPOC"
        p = p / f"tic_{int(r.tic_id):016d}.parquet"
        if p.exists():
            frames.append((read_parquet(p)[0], sec))
    if not frames:
        return {"ok": False, "error": "no local light curve"}
    windows = signal_windows(
        getattr(r, "detrend_windows_json", None),
        r.detrend_window_days,
        dur,
        [s for _, s in frames],
        cfg.preprocess,
    )
    lc = flatten_for_signal(
        frames,
        cfg.preprocess,
        windows=windows,
        period_days=float(r.period_days),
        t0_btjd=float(r.t0_btjd),
        duration_days=dur,
    )
    if len(lc) == 0:
        return {"ok": False, "error": "empty light curve after detrending"}
    dt = np.diff(lc.time)
    exptime = float(np.median(dt[dt > 0])) if (dt > 0).any() else 120 / 86400
    ph = phase_days(lc.time, r.period_days, r.t0_btjd)
    sel = np.abs(ph) < 2.5 * dur
    res = run_fpp(
        tic_id=int(r.tic_id),
        sectors=sorted(apertures),
        depth_ppm=float(r.fit_depth_ppm),
        period_days=float(r.period_days),
        duration_days=dur,
        apertures=apertures,
        phase_days=ph[sel],
        flux=lc.flux[sel].astype(float),
        flux_err=lc.flux_err[sel].astype(float),
        workdir=root / "cache" / "fpp" / f"sig{int(r.signal_id)}",
        exptime_days=exptime,
        dilution_corrected=True,
        n_draws=cfg.vetting.fpp_draws,
        repeats=cfg.vetting.fpp_repeats,
        timeout_s=cfg.vetting.fpp_timeout_s,
    )
    return {**res, "exptime_days": exptime}
