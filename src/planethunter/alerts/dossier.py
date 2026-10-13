"""Self-contained HTML dossier per candidate: plots, vetting, crossmatch, provenance.

No network. Reads local Parquet and DuckDB. Images embedded as base64 so it opens offline.
"""

from __future__ import annotations

import base64
import html
import io
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from planethunter.config import Config
from planethunter.db.store import connect
from planethunter.ingest.lightcurves import read_parquet
from planethunter.preprocess.clean import bin_lightcurve, flatten_for_signal, signal_windows
from planethunter.vetting.basic import DESAT_BIT, epoch_index, phase_days, trapezoid

LINKS = {
    "ExoFOP": "https://exofop.ipac.caltech.edu/tess/target.php?id={tic}",
    "Exoplanet Archive": "https://exoplanetarchive.ipac.caltech.edu/overview/TIC%20{tic}",
    'SIMBAD (30")': (
        "https://simbad.cds.unistra.fr/simbad/sim-coo?Coord={ra}+{dec}&Radius=30&Radius.unit=arcsec"
    ),
}


def _fig_to_b64(fig) -> str:
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _binned(x: np.ndarray, y: np.ndarray, width: float) -> tuple[np.ndarray, np.ndarray]:
    if len(x) == 0:
        return x, y
    edges = np.arange(x.min(), x.max() + width, width)
    idx = np.digitize(x, edges)
    xs, ys = [], []
    for i in np.unique(idx):
        m = idx == i
        if m.sum() >= 3:
            xs.append(x[m].mean())
            ys.append(np.median(y[m]))
    return np.array(xs), np.array(ys)


def vetted_period(period_days: float, tests: list[dict]) -> float:
    """Period actually vetted: P/2 when basic vetting halved the signal (`period_halved`)."""
    t = next((t for t in tests if t.get("name") == "period_halved"), None)
    if t and t.get("value"):
        return float(t["value"])
    return float(period_days)


def _ld_model(tests: list[dict], P: float, x: np.ndarray) -> np.ndarray | None:
    """batman model of the limb-darkened fit (kdr25_grazing extra) on phase times x (days)."""
    t = next((t for t in tests if t.get("name") == "kdr25_grazing"), None)
    ld = (t or {}).get("extra") or {}
    if not ld.get("k") or ld.get("unconstrained"):
        return None
    try:
        import batman

        p = batman.TransitParams()
        p.t0, p.per, p.rp, p.a = ld["center_days"], P, ld["k"], ld["a_rs"]
        p.inc = math.degrees(math.acos(min(1.0, ld["b"] / ld["a_rs"])))
        p.ecc, p.w, p.limb_dark, p.u = 0.0, 90.0, "quadratic", list(ld["u"])
        return batman.TransitModel(p, x).light_curve(p)
    except Exception:  # plotting aid only
        return None


def _plots(
    sig: pd.Series, vet: pd.Series, lc, raw: pd.DataFrame, tests: list[dict] | None = None
) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tests = tests or []
    P = vetted_period(sig["period_days"], tests)
    t0, dur = sig["t0_btjd"], sig["duration_hours"] / 24
    t, f = lc.time, lc.flux.astype(float)
    ph = phase_days(t, P, t0)
    n_ep = epoch_index(t, P, t0)
    out: dict[str, str] = {}

    # 1. full light curve
    fig, ax = plt.subplots(figsize=(12, 3.2))
    b = bin_lightcurve(lc, 30)
    ax.plot(t, f, ".", ms=1, color="0.75", rasterized=True)
    ax.plot(b.time, b.flux, ".", ms=3, color="k")
    for e in np.unique(n_ep[np.abs(ph) < dur]):
        ax.axvline(t0 + e * P, color="tab:red", alpha=0.5, lw=1)
    dumps = raw["time"].to_numpy()[(raw["quality"].to_numpy() & DESAT_BIT) != 0]
    for d in dumps:
        ax.axvline(d, color="tab:blue", alpha=0.25, lw=0.6, ls=":")
    ax.set_xlabel("BTJD")
    ax.set_ylabel("normalized flux")
    ax.set_title("Detrended light curve (red: transits; dotted blue: momentum dumps)")
    out["lc"] = _fig_to_b64(fig)

    # 2. phase fold with trapezoid
    sel = np.abs(ph) < 3 * dur
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(ph[sel] * 24, f[sel], ".", ms=2, color="0.7", rasterized=True)
    xb, yb = _binned(ph[sel] * 24, f[sel], max(dur * 24 / 12, 0.1))
    ax.plot(xb, yb, "o", ms=4, color="k")
    if pd.notna(vet.get("fit_depth_ppm")) and pd.notna(vet.get("fit_t14_hours")):
        xm = np.linspace(-3 * dur, 3 * dur, 600)
        t14 = vet["fit_t14_hours"] / 24
        model = trapezoid(xm, vet["fit_depth_ppm"] * 1e-6, t14, vet["fit_tau_frac"] * t14, 0.0)
        ax.plot(xm * 24, model * np.median(f[~sel]), color="tab:red", lw=2, label="trapezoid")
        ld = _ld_model(tests, P, xm)
        if ld is not None:
            ax.plot(xm * 24, ld * np.median(f[~sel]), color="tab:blue", lw=1.5, ls="--",
                    label="limb-darkened (batman)")  # fmt: skip
        ax.legend(loc="lower right", fontsize=8)
    ax.set_xlabel("hours from mid-transit")
    ax.set_ylabel("flux")
    ax.set_title(f"Folded at P = {P:.5f} d")
    out["fold"] = _fig_to_b64(fig)

    # 3. odd / even and 4. secondary
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.6), sharey=True)
    for ax, (label, m) in zip(
        axes[:2], [("Odd", n_ep % 2 == 1), ("Even", n_ep % 2 == 0)], strict=True
    ):
        s2 = sel & m
        ax.plot(ph[s2] * 24, f[s2], ".", ms=2, color="0.7")
        xb, yb = _binned(ph[s2] * 24, f[s2], max(dur * 24 / 10, 0.1))
        ax.plot(xb, yb, "o", ms=4, color="k")
        ax.set_title(f"{label} transits")
        ax.set_xlabel("hours")
    ph2 = ((t - t0) % P) - 0.5 * P
    s3 = np.abs(ph2) < 3 * dur
    axes[2].plot(ph2[s3] * 24, f[s3], ".", ms=2, color="0.7")
    xb, yb = _binned(ph2[s3] * 24, f[s3], max(dur * 24 / 10, 0.1))
    axes[2].plot(xb, yb, "o", ms=4, color="k")
    axes[2].set_title("Phase 0.5 (secondary eclipse?)")
    axes[2].set_xlabel("hours from phase 0.5")
    out["oddeven"] = _fig_to_b64(fig)

    # 5. depth per transit
    core = np.abs(ph) < 0.4 * dur
    base = np.median(f[np.abs(ph) > 1.5 * dur])
    eps, ds = [], []
    for e in np.unique(n_ep[core]):
        m = core & (n_ep == e)
        if m.sum() >= 3:
            eps.append(t0 + e * P)
            ds.append((base - f[m].mean()) * 1e6)
    if eps:
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(eps, ds, "o", color="k")
        ax.axhline(np.mean(ds), color="tab:red", ls="--")
        ax.set_xlabel("transit BTJD")
        ax.set_ylabel("depth (ppm)")
        ax.set_title("Depth per transit")
        out["per_transit"] = _fig_to_b64(fig)
    return out


def _table(rows: list[list[str]], header: list[str]) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in header)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def _fmt(x: object, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}g}" if abs(x) < 1e4 else f"{x:.0f}"
    return html.escape(str(x))


CSS = """
:root{--bg:#fff;--fg:#1b1f24;--muted:#5b6470;--line:#d8dde3;--ok:#1a7f37;--bad:#c62828;--warn:#9a6700}
@media (prefers-color-scheme:dark){:root{--bg:#0f1419;--fg:#e6e8eb;--muted:#9aa4af;--line:#2a313a;
--ok:#3fb950;--bad:#f85149;--warn:#d29922}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:1100px;
margin:0 auto;padding:16px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px;border-bottom:1px solid var(--line)}
.muted{color:var(--muted)}table{border-collapse:collapse;width:100%;font-size:14px;overflow-x:auto;
display:block}td,th{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;
vertical-align:top}img{max-width:100%;background:#fff;border-radius:4px}.ok{color:var(--ok)}
.bad{color:var(--bad);font-weight:600}.warn{color:var(--warn)}.pill{display:inline-block;padding:2px 8px;
border-radius:10px;border:1px solid var(--line);margin-right:6px}
"""


def build_dossier(root: Path, cfg: Config, signal_id: int) -> Path:
    con = connect(root)
    q = """
        SELECT s.*, c.match_class, c.host_known, c.matched_name, c.notes AS xm_notes,
               c.mirror_ages_json, c.n_host_objects, c.n_nearby_objects,
               v.score, v.verdict, v.vetoed_by, v.failed, v.deep_pending, v.fit_depth_ppm,
               v.fit_t14_hours, v.fit_tau_frac, v.fit_rp_rs, v.tests_json,
               k.severity, t.ra_deg, t.dec_deg, t.tmag, t.teff_k, t.radius_rsun, t.mass_msun,
               t.crowdsap
        FROM signals s
        LEFT JOIN crossmatch c USING (signal_id)
        LEFT JOIN vetting v USING (signal_id)
        LEFT JOIN candidates k USING (signal_id)
        LEFT JOIN targets t ON t.tic_id = s.tic_id
        WHERE s.signal_id = ?
    """
    df = con.execute(q, [signal_id]).df()
    if df.empty:
        con.close()
        raise KeyError(f"signal_id {signal_id} does not exist")
    r = df.iloc[0]
    sectors = {int(x) for x in str(r["sectors"]).split(",") if x}
    paths = con.execute(
        "SELECT path, sector FROM lightcurves WHERE tic_id = ? AND author = ?",
        [int(r["tic_id"]), r["author"]],
    ).fetchall()
    con.close()
    frames = [read_parquet(root / p)[0] for p, sec in paths if sec in sectors]
    secs = [sec for p, sec in paths if sec in sectors]
    tests = json.loads(r["tests_json"]) if isinstance(r["tests_json"], str) else []
    # Same light curve as basic vetting (pipeline._vet_target): per-sector search-time windows
    # (>= min_window_durations x T14), transits masked, at the vetted period (P/2 if halved).
    dur = r["duration_hours"] / 24
    win_json = r.get("detrend_windows_json")
    windows = signal_windows(
        win_json if isinstance(win_json, str) else None,
        None if pd.isna(r["detrend_window_days"]) else float(r["detrend_window_days"]),
        dur,
        secs,
        cfg.preprocess,
    )
    lc = flatten_for_signal(
        list(zip(frames, secs, strict=True)),
        cfg.preprocess,
        windows=windows,
        period_days=vetted_period(r["period_days"], tests),
        t0_btjd=float(r["t0_btjd"]),
        duration_days=dur,
    )
    w = ", ".join(f"s{s}: {v:.2f}" for s, v in sorted(windows.items()))
    raw = pd.concat(frames, ignore_index=True)
    imgs = _plots(r, r, lc, raw, tests)

    tic = int(r["tic_id"])
    # fit_rp_rs = k used by the radius test (limb-darkened fit, or sqrt(depth) as fallback).
    k = r["fit_rp_rs"] if pd.notna(r.get("fit_rp_rs")) else None
    if k is None and pd.notna(r["fit_depth_ppm"]):
        k = math.sqrt(max(r["fit_depth_ppm"], 0) * 1e-6)
    rp = k * r["radius_rsun"] * 109.076 if k and pd.notna(r["radius_rsun"]) else float("nan")
    test_rows = []
    for tr in tests:
        status = (
            '<span class="bad">VETO</span>'
            if tr["veto"]
            else '<span class="ok">pass</span>'
            if tr["passed"]
            else '<span class="bad">fail</span>'
            if tr["passed"] is False
            else '<span class="warn">no data</span>'
        )
        test_rows.append(
            [
                html.escape(tr["name"]),
                _fmt(tr["value"]),
                _fmt(tr["threshold"]),
                status,
                html.escape(tr["note"] or ""),
            ]
        )
    for name in str(r["deep_pending"] or "").split(","):
        if name:
            test_rows.append(
                [
                    html.escape(name),
                    "—",
                    "—",
                    '<span class="warn">pending</span>',
                    "deep vetting (network): not run yet",
                ]
            )
    ages = json.loads(r["mirror_ages_json"]) if isinstance(r["mirror_ages_json"], str) else {}
    age_rows = [[k, _fmt(v, 2) + " h" if v is not None else "MISSING"] for k, v in ages.items()]
    links = " · ".join(
        f'<a href="{html.escape(u.format(tic=tic, ra=r["ra_deg"], dec=r["dec_deg"]))}">{k}</a>'
        for k, u in LINKS.items()
    )
    sev = r["severity"] if isinstance(r["severity"], str) else "—"
    head_rows = [
        ["TIC", str(tic)],
        ["Tmag", _fmt(r["tmag"])],
        ["Teff (K)", _fmt(r["teff_k"])],
        ["R* (R☉)", _fmt(r["radius_rsun"])],
        ["M* (M☉)", _fmt(r["mass_msun"])],
        ["CROWDSAP", _fmt(r["crowdsap"])],
        ["Sectors", html.escape(str(r["sectors"]))],
        ["Period (d)", f"{r['period_days']:.6f} ± {_fmt(r['period_err_days'])}"],
        ["Vetted period (d)", f"{vetted_period(r['period_days'], tests):.6f}"],
        ["T0 (BTJD)", f"{r['t0_btjd']:.5f}"],
        ["Fitted depth (ppm)", _fmt(r["fit_depth_ppm"], 4)],
        ["T14 (h)", _fmt(r["fit_t14_hours"])],
        ["Rp (R⊕)", _fmt(rp)],
        ["SDE / SNR", f"{r['sde']:.1f} / {r['snr']:.1f}"],
        ["Transits with data", str(r["n_transits"])],
        ["Applied alias factor", _fmt(r.get("alias_factor"))],
    ]
    diff_imgs = sorted((root / "cache" / "diffimg").glob(f"sig{signal_id}_s*.png"))
    diff_html = "".join(
        f"<h2>TPF difference image ({p.stem.split('_')[-1]})</h2>"
        f'<img src="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}" alt="diff">'
        for p in diff_imgs
    )
    # "Candidate" only for NEW; known objects and vetting failures are "Signal".
    heading = (
        "Candidate" if r["match_class"] == "NEW" and r["verdict"] == "PASS_BASIC" else "Signal"
    )
    next_step = (
        "Run deep vetting (TPF difference image, Gaia neighbors, FPP). If it passes, "
        "review and submit as a CTOI on ExoFOP with this dossier."
        if r["match_class"] == "NEW" and r["verdict"] == "PASS_BASIC"
        else "None: known signal or failed vetting."
    )
    body = f"""
<h1>{heading} TIC {tic} · P = {r["period_days"]:.4f} d</h1>
<p class="muted">signal_id {signal_id} · generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC ·
vocabulary: candidate (not a discovery)</p>
<p><span class="pill">severity {html.escape(sev)}</span>
<span class="pill">crossmatch {html.escape(str(r["match_class"]))}</span>
<span class="pill">vetting {html.escape(str(r["verdict"]))} · score {_fmt(r["score"], 2)}</span>
<span class="pill">known host: {"yes" if r["host_known"] else "no"}</span></p>
<p>{links}</p>
<h2>Parameters</h2>{_table(head_rows, ["", ""])}
<h2>Light curve</h2><img src="data:image/png;base64,{imgs["lc"]}" alt="light curve">
<h2>Folded transit</h2><img src="data:image/png;base64,{imgs["fold"]}" alt="folded">
<h2>Odd, even and secondary</h2><img src="data:image/png;base64,{imgs["oddeven"]}" alt="odd even">
{f'<h2>Depth per transit</h2><img src="data:image/png;base64,{imgs["per_transit"]}" alt="per transit">' if "per_transit" in imgs else ""}
{diff_html}
<h2>Vetting</h2>{_table(test_rows, ["test", "value", "threshold", "result", "note"])}
<h2>Crossmatch</h2>
<p>Class <b>{html.escape(str(r["match_class"]))}</b>; objects on host: {r["n_host_objects"]};
neighbors within {cfg.crossmatch.nearby_radius_arcsec:.0f}": {r["n_nearby_objects"]};
matched: {html.escape(str(r["matched_name"] or "—"))}.</p>
<p class="muted">{html.escape(str(r["xm_notes"] or ""))}</p>
{_table(age_rows, ["mirror", "age at crossmatch"])}
<h2>Next action</h2><p>{next_step}</p>
<h2>Provenance</h2>
<p class="muted">run_id {html.escape(str(r["run_id"]))} · pipeline {html.escape(str(r["pipeline_version"]))}
· params {html.escape(str(r["params_hash"]))} · author {html.escape(str(r["author"]))} ·
detrending windows (d) {html.escape(w)}</p>
"""
    doc = (
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Dossier TIC {tic}</title><style>{CSS}</style></head><body>{body}</body></html>"
    )
    dest = root / "dossiers" / f"tic{tic}_sig{signal_id}.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    con = connect(root)
    con.execute(
        "UPDATE candidates SET dossier_path = ? WHERE signal_id = ?", [str(dest), signal_id]
    )
    con.close()
    return dest
