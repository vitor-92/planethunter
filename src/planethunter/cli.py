"""PlanetHunter CLI. `uv run planethunter --help`."""

from __future__ import annotations

import pandas as pd
import typer

from planethunter.config import data_dir, load_config

app = typer.Typer(help="Search for exoplanet candidates in TESS data.", no_args_is_help=True)
ingest_app = typer.Typer(
    help="Download light curves from MAST to local Parquet.", no_args_is_help=True
)
mirrors_app = typer.Typer(help="Local catalog mirrors.", no_args_is_help=True)
bench_app = typer.Typer(help="Recall benchmark on known TOIs.", no_args_is_help=True)
app.add_typer(ingest_app, name="ingest")
app.add_typer(mirrors_app, name="mirrors")
app.add_typer(bench_app, name="benchmark")


@app.callback()
def _main() -> None:
    """Load the repo-root .env without overriding the environment (alert tokens,
    PLANETHUNTER_MAX_WORKERS). Values are never logged."""
    from planethunter.alerts.notify import load_env

    load_env()


pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def _parse_ints(s: str | None) -> list[int] | None:
    return [int(x) for x in s.split(",") if x.strip()] if s else None


@ingest_app.command("sector")
def ingest_sector_cmd(
    sector: int,
    limit: int = typer.Option(None, help="Only the first N targets (testing)."),
    tics: str = typer.Option(None, help="Comma-separated list of TIC IDs."),
    workers: int = typer.Option(8, help="Concurrent downloads (be gentle with MAST)."),
) -> None:
    """SPOC 2-min light curves for an entire sector."""
    from planethunter.ingest.mast import ingest_sector
    from planethunter.pipeline import register_lightcurves

    root = data_dir()
    tic_set = set(_parse_ints(tics)) if tics else None
    rep = ingest_sector(sector, root, limit=limit, tic_ids=tic_set, max_workers=workers)
    from planethunter.pipeline import discover

    register_lightcurves(
        root, [p for ps in discover(root, sector=sector, tic_ids=tic_set).values() for p in ps]
    )
    typer.echo(rep.summary())
    for url, err in rep.errors[:10]:
        typer.echo(f"  ERROR {url.rsplit('/', 1)[-1]}: {err}")


@ingest_app.command("target")
def ingest_target_cmd(tic: int, sectors: str = typer.Option(None, help="E.g.: 1,4,8")) -> None:
    """All SPOC 2-min sectors for one target."""
    from planethunter.ingest.mast import ingest_target
    from planethunter.pipeline import discover, register_lightcurves

    root = data_dir()
    rep = ingest_target(tic, root, sectors=_parse_ints(sectors))
    register_lightcurves(root, discover(root, tic_ids={tic}).get(tic, []))
    typer.echo(rep.summary())


@mirrors_app.command("sync")
def mirrors_sync(
    source: str = typer.Option(None, help="Comma-separated sources (default: all)."),
    force: bool = typer.Option(False, help="Re-download static catalogs too."),
) -> None:
    """Sync the catalog mirrors (Archive, ExoFOP TOI/CTOI, exoplanet.eu, KOI, K2, VizieR
    EB and published-candidate catalogs). Static catalogs are skipped when up to date."""
    from planethunter.catalogs.mirrors import sync_all
    from planethunter.crossmatch.core import Source

    sources = [Source(x.strip()) for x in source.split(",")] if source else None
    for src, res in sync_all(data_dir(), sources=sources, force=force).items():
        typer.echo(f"{src.value:22s} {res}")


@mirrors_app.command("status")
def mirrors_status() -> None:
    """Freshness and provenance of each mirror. Exit code 1 if any source is missing or
    stale for its policy (that blocks NEW classification and alerts)."""
    from planethunter.catalogs.mirrors import mirror_manifest
    from planethunter.crossmatch.core import Source

    cfg = load_config().crossmatch
    manifest = mirror_manifest(data_dir())
    bad = False
    for src in Source:
        info = manifest.get(src)
        limit = cfg.max_age_hours(src.value)
        policy = "static" if limit is None else f"<{limit:.0f} h"
        if info is None:
            flag, age_s, rows, sha, fname = "MISSING", "-", "-", "-", "-"
        else:
            age = info["age_hours"]
            if not info["version_ok"]:
                flag = "VERSION"
            elif limit is not None and age > limit:
                flag = "STALE"
            else:
                flag = "ok"
            age_s, rows = f"{age:.1f} h", str(info["n_rows"])
            sha, fname = info["sha256"][:12], info["file"]
        bad |= flag != "ok"
        typer.echo(
            f"{src.value:20s} {flag:8s} {policy:>7s} age={age_s:>8s} rows={rows:>7s} "
            f"sha256={sha} {fname}"
        )
    if bad:
        raise typer.Exit(1)


@app.command()
def search(
    sector: int = typer.Option(None, help="Sector to search."),
    tics: str = typer.Option(None, help="Comma-separated TIC IDs."),
    all_sectors: bool = typer.Option(False, help="Stitch all sectors of each target."),
    workers: int = typer.Option(
        None, help="Parallel processes (default: n_cpus - 1; capped by PLANETHUNTER_MAX_WORKERS)."
    ),
    resume: str = typer.Option(None, help="run_id to resume."),
    null: str = typer.Option(
        None,
        help="Null run for the false-alarm rate (Thompson+2018): 'inverted' or 'scrambled'.",
    ),
) -> None:
    """Preprocess + iterative TLS in parallel. Writes to `signals`."""
    from planethunter.pipeline import run_search

    tic_set = set(_parse_ints(tics)) if tics else None
    s = run_search(
        data_dir(),
        load_config(),
        sector=sector,
        tic_ids=tic_set,
        all_sectors=all_sectors,
        workers=workers,
        resume_run_id=resume,
        null_mode=null,
    )
    typer.echo(
        f"run_id={s.run_id} targets={s.n_targets} done={s.n_done} signals={s.n_signals} "
        f"errors={s.n_errors} time={s.elapsed_s / 60:.1f} min"
    )


@app.command()
def crossmatch(run: str) -> None:
    """Classify a run's signals against the local mirrors (no network)."""
    from planethunter.pipeline import run_crossmatch

    out = run_crossmatch(data_dir(), load_config(), run)
    typer.echo(out["match_class"].value_counts().to_string() if len(out) else "no signals")


@app.command()
def vet(run: str, workers: int = typer.Option(None)) -> None:
    """Basic vetting (no network) of a run's signals and promotion to candidates."""
    from planethunter.pipeline import promote_candidates, run_vetting, vetting_validation

    root, cfg = data_dir(), load_config()
    out = run_vetting(root, cfg, run, workers=workers)
    typer.echo(f"signals vetted: {len(out)}")
    typer.echo(vetting_validation(root, run).to_string(index=False))
    cands = promote_candidates(root, cfg, run)
    typer.echo(
        f"candidates: {len(cands)} "
        + str(cands["severity"].value_counts().to_dict() if len(cands) else {})
    )


REVIEW_STATUS = ("approved", "rejected", "follow_up")
REJECT_REASONS = ("eb", "blend", "systematic", "noise", "already_known", "other")


@app.command()
def review(
    signal_id: int,
    status: str = typer.Argument(..., help="approved | rejected | follow_up"),
    reason: str = typer.Option(
        None, help="If rejected: eb, blend, systematic, noise, already_known, other."
    ),
    note: str = typer.Option("", help="Free-form comment."),
) -> None:
    """Record the human review of a candidate (becomes a label for the ML model)."""
    from planethunter.db.store import connect

    if status not in REVIEW_STATUS:
        raise typer.BadParameter(f"status must be one of {REVIEW_STATUS}")
    if status == "rejected" and reason not in REJECT_REASONS:
        raise typer.BadParameter(f"rejection requires --reason in {REJECT_REASONS}")
    full_note = f"[{reason}] {note}".strip() if reason else note
    con = connect(data_dir())
    n = con.execute(
        "UPDATE candidates SET review_status = ?, review_note = ?, reviewed_at = now() "
        "WHERE signal_id = ? RETURNING signal_id",
        [status, full_note, signal_id],
    ).fetchall()
    con.close()
    if not n:
        raise typer.BadParameter(f"signal_id {signal_id} is not in the candidate queue")
    typer.echo(f"signal {signal_id}: {status} {full_note}")


@app.command()
def calibrate(
    runs: str = typer.Option(
        None,
        help="Comma-separated labeled run_ids (default: latest run per sector with "
        "KNOWN_PLANET/KNOWN_FP matches).",
    ),
    null_runs: str = typer.Option(
        None,
        help="Comma-separated null run_ids (search mode null-inverted/null-scrambled); all "
        "their vetted signals are class 0. Default: latest null run per sector; 'none' = skip.",
    ),
    recompute: bool = typer.Option(
        False,
        help="Re-vet every run with the current code (default: stored vetting.tests_json; "
        "runs without vetting rows are always re-vetted). No DB writes.",
    ),
    workers: int = typer.Option(2, help="Processes used to recompute vetting."),
    seed: int = typer.Option(0, help="Seed for the CV folds and the solver."),
    c_value: float = typer.Option(
        None, "--C", help="Fixed regularization (default: grid search with grouped CV)."
    ),
    positive_alias: str = typer.Option(
        "any", help="'1' keeps only planets matched at alias 1 (drops 1/2, 2, unknown)."
    ),
    out: str = typer.Option(None, help="Model path (default: data/models/vetting_lr.json)."),
    dry_run: bool = typer.Option(False, help="Train and report only; do not write the model."),
    repromote: bool = typer.Option(
        False, help="After saving, rescore p_rank/p_abs and repromote candidates of the runs."
    ),
) -> None:
    """Train the ranking probability p_rank (planet vs. false positive / false alarm).

    One command: builds the dataset (KNOWN_PLANET = 1; KNOWN_FP and null-run signals = 0),
    picks C by grouped CV, reports nested out-of-fold metrics against the deterministic score,
    derives the P2/P1 operating points from out-of-fold recall on known planets, and writes
    the model JSON with full provenance.
    """
    from pathlib import Path

    from planethunter.ml.calibrate import (
        build_dataset,
        default_runs,
        null_vetting_supported,
        save_model,
        train,
    )

    root, cfg = data_dir(), load_config()
    def_runs, def_null = default_runs(root)
    run_list = [r.strip() for r in runs.split(",") if r.strip()] if runs else def_runs
    if null_runs and null_runs.strip().lower() == "none":
        null_list: list[str] = []
    elif null_runs:
        null_list = [r.strip() for r in null_runs.split(",") if r.strip()]
    else:
        null_list = def_null
        if null_list and not null_vetting_supported():
            typer.echo(
                f"skipping null runs {null_list}: basic vetting does not re-apply the null "
                "transform yet, so their features would come from the original light curves"
            )
            null_list = []
    typer.echo(f"labeled runs: {run_list}\nnull runs: {null_list or 'none'}")
    df = build_dataset(
        root,
        cfg,
        run_list,
        null_runs=null_list,
        recompute=recompute,
        workers=workers,
        positive_alias=positive_alias,
    )
    typer.echo(f"dataset: {len(df)} signals, {df['tic_id'].nunique()} stars")
    typer.echo(df.groupby(["label", "source"]).size().to_string())
    sev = cfg.severity
    model = train(
        df,
        C=c_value,
        seed=seed,
        p2_recall=sev.p2_recall_target,
        p1_recall=sev.p1_recall_target,
        p1_fpr_max=sev.p1_fpr_max,
        sev_cfg=sev,
        provenance={
            "runs": run_list,
            "null_runs": null_list,
            "positive_alias": positive_alias,
            "features_from": "recomputed" if recompute else "stored vetting.tests_json",
            "config_params_hash": cfg.params_hash(),
        },
    )
    m, ops = model["metrics_oof"], model["operating_points"]
    typer.echo(
        f"C = {model['C']} ({model['C_selection']['method']}); nested out-of-fold: "
        f"ROC-AUC model {m.get('roc_auc_model', float('nan')):.3f} vs score "
        f"{m.get('roc_auc_score', float('nan')):.3f} | PR-AUC model "
        f"{m.get('pr_auc_model', float('nan')):.3f} vs score "
        f"{m.get('pr_auc_score', float('nan')):.3f} | Brier {m.get('brier_model', 0):.3f} "
        f"(uncalibrated {m.get('brier_uncalibrated', 0):.3f})"
    )
    typer.echo(
        f"operating points: P2 cut {ops['p2_cut']:.3f} (recall {ops['recall_p2']:.2f}, "
        f"FPR {ops['fpr_p2']:.3f}); P1 cut {ops['p1_cut']:.3f} (recall {ops['recall_p1']:.2f}, "
        f"FPR {ops['fpr_p1']:.3f})"
    )
    for src, d in ops.get("by_source", {}).items():
        typer.echo(
            f"  {src:<20} n={d['n']:<5} label={d['label']} mean p={d['mean_p']:.2f} "
            f">=P2 cut {d['rate_p2']:.2f} >=P1 cut {d['rate_p1']:.2f}"
        )
    rec = model["severity_recall_oof"]
    typer.echo(f"severity on known planets (as NEW, no deep vetting): {rec['planets']}")
    typer.echo(f"severity on negatives (as NEW, no deep vetting): {rec['negatives']}")
    if dry_run:
        typer.echo(f"dry run: model {model['model_version']} not saved")
        return
    path = save_model(model, root, Path(out) if out else None)
    typer.echo(f"model {model['model_version']} saved to {path}")
    if repromote and not out:
        from planethunter.pipeline import promote_candidates

        for run in run_list:
            cands = promote_candidates(root, cfg, run)
            counts = cands["severity"].value_counts().to_dict() if len(cands) else {}
            typer.echo(f"repromoted {run}: {counts}")


@app.command("vet-deep")
def vet_deep(
    run: str = typer.Argument(None),
    workers: int = typer.Option(
        None, help="Candidates in parallel (default: vetting.deep_workers)."
    ),
    force: bool = typer.Option(False, help="Also redo candidates already evaluated."),
) -> None:
    """Deep vetting of the candidates (TPF, Gaia, SIMBAD, other sectors, FPP; cached).

    Resumable: writes each candidate as it finishes and skips those already evaluated.
    """
    from planethunter.pipeline import promote_candidates, run_deep_vetting

    root, cfg = data_dir(), load_config()
    out = run_deep_vetting(root, cfg, run, workers=workers, force=force)
    typer.echo(
        out[["signal_id", "verdict", "score", "failed"]].to_string(index=False)
        if len(out)
        else "no candidates"
    )
    if run:
        promote_candidates(root, cfg, run)


@app.command("candidates")
def candidates_cmd(run: str = typer.Argument(None)) -> None:
    """NEW candidates that passed basic vetting (run `vet` first)."""
    from planethunter.pipeline import candidate_table

    df = candidate_table(data_dir(), run)
    typer.echo(df.to_string(index=False) if len(df) else "no candidates")


@app.command("run-target")
def run_target(tic: int, sectors: str = typer.Option(None), skip_ingest: bool = False) -> None:
    """End to end for one target: ingest, multi-sector search, crossmatch, basic vetting,
    and a dossier for each signal above the minimum SDE. Prints signal_id and dossier paths."""
    from planethunter.alerts.dossier import build_dossier
    from planethunter.ingest.mast import ingest_target
    from planethunter.pipeline import connect, run_crossmatch, run_search, run_vetting

    root, cfg = data_dir(), load_config()
    if not skip_ingest:
        typer.echo(ingest_target(tic, root, sectors=_parse_ints(sectors)).summary())
    s = run_search(root, cfg, tic_ids={tic}, all_sectors=True, workers=1)
    xm = run_crossmatch(root, cfg, s.run_id)
    run_vetting(root, cfg, s.run_id, workers=1)
    con = connect(root)
    df = con.execute(
        "SELECT s.signal_id, s.period_days, s.t0_btjd, s.depth_ppm, s.duration_hours, "
        "s.sde, s.snr, s.n_transits, c.match_class, c.matched_name, v.verdict, v.score "
        "FROM signals s LEFT JOIN crossmatch c USING (signal_id) "
        "LEFT JOIN vetting v USING (signal_id) WHERE s.run_id = ? ORDER BY s.sde DESC",
        [s.run_id],
    ).df()
    con.close()
    typer.echo(f"run_id={s.run_id}  {s.elapsed_s:.1f} s")
    typer.echo(df.to_string(index=False) if len(df) else "no signal above the minimum SDE")
    for sid in df.loc[df["sde"] >= cfg.vetting.sde_min, "signal_id"]:
        typer.echo(f"dossier for signal {int(sid)}: {build_dossier(root, cfg, int(sid))}")
    if len(xm) and (xm["match_class"] == "UNVERIFIED").any():
        typer.echo("WARNING: mirrors missing or stale; run `planethunter mirrors sync`.")


@app.command()
def dossier(signal_id: int) -> None:
    """Build the HTML dossier for a signal in data/dossiers/."""
    from planethunter.alerts.dossier import build_dossier

    typer.echo(build_dossier(data_dir(), load_config(), signal_id))


@app.command()
def alert(
    run: str = typer.Argument(None),
    send: bool = typer.Option(False, help="Actually send (Telegram/Discord from .env)."),
) -> None:
    """Build dossiers and alert on new P0/P1 candidates. Default: dry run into data/outbox/."""
    from planethunter.alerts.dossier import build_dossier
    from planethunter.alerts.notify import send_alerts
    from planethunter.pipeline import candidate_table

    root, cfg = data_dir(), load_config()
    for sid in candidate_table(root, run)["signal_id"]:
        build_dossier(root, cfg, int(sid))
    for o in send_alerts(root, cfg, run, dry_run=not send):
        typer.echo(f"signal {o.signal_id}: {o.channel} {o.status} {o.reason}")


@app.command("run-sector")
def run_sector(
    sector: int,
    limit: int = typer.Option(None, help="Only the first N targets (testing)."),
    skip_ingest: bool = False,
    send: bool = typer.Option(False, help="Actually send alerts."),
) -> None:
    """End to end: mirrors, ingest, search, crossmatch, vetting, candidates, alerts."""
    from planethunter.alerts.dossier import build_dossier
    from planethunter.alerts.notify import send_alerts
    from planethunter.catalogs.mirrors import load_known, sync_all
    from planethunter.ingest.mast import ingest_sector
    from planethunter.pipeline import (
        candidate_table,
        discover,
        promote_candidates,
        register_lightcurves,
        run_crossmatch,
        run_deep_vetting,
        run_search,
        run_vetting,
    )

    root, cfg = data_dir(), load_config()
    _, ages = load_known(root)

    # Sync if any mirror is missing or would expire during the run (per-source limit, 6 h margin).
    def _expiring(src, age) -> bool:
        limit = cfg.crossmatch.max_age_hours(getattr(src, "value", src))
        return age is None or (limit is not None and age > limit - 6)

    if any(_expiring(src, age) for src, age in ages.items()):
        typer.echo("syncing mirrors...")
        sync_all(root)
    if not skip_ingest:
        typer.echo(f"ingest: {ingest_sector(sector, root, limit=limit).summary()}")
    tics = set(list(discover(root, sector=sector))[:limit]) if limit else None
    register_lightcurves(
        root, [p for ps in discover(root, sector=sector, tic_ids=tics).values() for p in ps]
    )
    s = run_search(root, cfg, sector=sector, tic_ids=tics)
    typer.echo(
        f"search: run_id={s.run_id} targets={s.n_done} signals={s.n_signals} errors={s.n_errors}"
    )
    typer.echo(run_crossmatch(root, cfg, s.run_id)["match_class"].value_counts().to_dict())
    run_vetting(root, cfg, s.run_id)
    cands = promote_candidates(root, cfg, s.run_id)
    if len(cands):
        typer.echo("deep vetting of candidates (network)...")
        run_deep_vetting(root, cfg, s.run_id)
        cands = promote_candidates(root, cfg, s.run_id)
    typer.echo(f"candidates: {cands['severity'].value_counts().to_dict() if len(cands) else {}}")
    for sid in candidate_table(root, s.run_id)["signal_id"]:
        build_dossier(root, cfg, int(sid))
    for o in send_alerts(root, cfg, s.run_id, dry_run=not send):
        typer.echo(f"alert signal {o.signal_id}: {o.channel} {o.status} {o.reason}")


@bench_app.command("build")
def bench_build(
    sector: int,
    min_snr: float = 10.0,
    kind: str = typer.Option("planets", help="planets (CP/KP/PC) or fp (TFOPWG FP/FA)."),
) -> None:
    """Freeze the sector's TOI list (SNR >= min_snr, P <= 13 d)."""
    from planethunter.benchmark import build

    p = build(data_dir(), sector, min_snr=min_snr, kind=kind)
    typer.echo(f"{p}: {len(pd.read_csv(p))} TOIs")


@bench_app.command("run")
def bench_run(
    sector: int,
    workers: int = typer.Option(None),
    skip_ingest: bool = False,
    run: str = typer.Option(None, help="Evaluate an existing run instead of searching again."),
) -> None:
    """Ingest benchmark targets, search the sector, measure recall, report to docs/benchmarks/."""
    from planethunter.benchmark import bench_path, evaluate, report_markdown, write_report
    from planethunter.ingest.mast import ingest_sector
    from planethunter.pipeline import pipeline_version, run_search

    root, cfg = data_dir(), load_config()
    bench = pd.read_csv(bench_path(root, sector))
    tics = set(bench["tic_id"].astype(int))
    elapsed = None
    if run is None:
        if not skip_ingest:
            typer.echo(ingest_sector(sector, root, tic_ids=tics).summary())
        s = run_search(root, cfg, sector=sector, tic_ids=tics, workers=workers)
        run, elapsed = s.run_id, s.elapsed_s
    res = evaluate(root, cfg, sector, run)
    pv = pipeline_version()
    md = report_markdown(res, sector, run, cfg, elapsed, pv)
    out = write_report(md, sector, pv)
    res.to_csv(root / "benchmark" / f"result_{run}.csv", index=False)
    typer.echo(md)
    typer.echo(f"report: {out}")


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
