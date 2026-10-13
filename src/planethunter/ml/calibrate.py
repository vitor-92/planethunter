"""Ranking probability of being a planet, learned from signals with known answers.

What it is: a regularized logistic regression on the basic-vetting test values. Positives are
signals matched to confirmed/known planets (KNOWN_PLANET: Archive, TOI CP/KP, exoplanet.eu);
negatives are cataloged false positives (KNOWN_FP: TFOPWG FP and the TESS EB catalog) and,
when available, every vetted signal of a null search run (search_runs.mode "null-inverted" /
"null-scrambled"), which are false alarms by construction. Only basic-vetting tests are used:
deep-vetting tests do not exist for known objects.

Two probabilities (docs/PLAN.md §7):
- ``p_rank`` (stored in vetting.p_planet): Platt-calibrated on out-of-fold logits, so it is a
  probability under the *training* class mix (``train_prior``). Severity uses it only through
  two operating points derived from out-of-fold recall on KNOWN_PLANET (P2 and P1 cuts, kept in
  the model JSON). The ML never raises severity; it only lowers it (alerts/severity.py).
- ``p_abs`` (vetting.p_abs, display only): p_rank re-weighted from the training prior to an
  assumed prior for NEW signals (``severity.new_prior``, default 0.05):
  logit(p_abs) = logit(p_rank) + logit(new_prior) - logit(train_prior). The prior is an
  assumption, not a measurement.

Model choices (code audit 2026-10-10, B8):
- Unweighted fit (no class_weight="balanced"); Platt scaling on out-of-fold logits is the
  calibration step (Niculescu-Mizil & Caruana 2005: Platt beats isotonic below ~1000 cases).
- Two-sided duration feature |log10(T_obs/T_pred)|: long durations point to wrong stellar
  radii or systematics, not to planets (the signed feature had coefficient +0.30).
- secondary_sigma clipped at >= 0 (a negative "secondary" is noise); the magnitude of the
  negative part is an optional separate noise feature.
- tau/T14 floored at TAU_FRAC_FLOOR = 0.05: the ingress is not resolved below one 10-min bin
  for a 3-4 h transit (10/200 ~ 0.05), and the trapezoid fit sits at its 0.01 bound for
  box-shaped noise (14 % of NEW vs 3 % of planets). Below the floor the value carries no
  physical information, only fit-bound leverage for the linear term.
- Missing-value flags are merged into groups (``no_epochs``: odd-even/consistency/edges/
  secondary/shape unavailable; ``no_star``: no stellar radius or predicted duration), kept only
  with >= MIN_FLAG_COUNT occurrences of each value, and not standardized.
- C chosen on a small grid by GroupKFold-by-TIC log-loss; reported metrics come from nested
  CV (outer GroupKFold by TIC, inner grid search), so no star is ever in train and test.

Inference is pure numpy from a JSON file (data/models/vetting_lr.json); < 1 ms per signal.
Schema 1 models (before 2026-10-10) still load and predict, with fallback cuts.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_PATH_REL = Path("models") / "vetting_lr.json"
MODEL_SCHEMA = 2
TAU_FRAC_FLOOR = 0.05
C_GRID: tuple[float, ...] = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0)
MIN_FLAG_COUNT = 20
NULL_MODES: tuple[str, ...] = ("null-inverted", "null-scrambled")
LABELED_CLASSES = ("KNOWN_PLANET", "KNOWN_FP")

# (feature name, vetting test, transform). Transforms are self-describing strings so the
# model JSON fully specifies inference: log | log_p | raw | abs_log | clip:lo:hi |
# neg_clip:hi (magnitude of the negative part) | floor:x.
FEATURES: list[tuple[str, str, str]] = [
    ("log_sde", "sde", "log"),
    ("log_snr", "snr", "log"),
    ("log_n_transits", "n_transits", "log"),
    ("odd_even_sigma", "odd_even", "clip:0:10"),
    ("secondary_sigma", "secondary", "clip:0:10"),
    ("secondary_scan_sigma", "secondary_scan", "clip:-10:10"),
    ("tau_frac", "shape", f"floor:{TAU_FRAC_FLOOR}"),
    ("log_radius_rearth", "radius", "log"),
    ("abs_log_duration_ratio", "duration", "abs_log"),
    ("centroid_offset_px", "centroid", "clip:0:10"),
    ("edges_dumps_frac", "edges_dumps", "raw"),
    ("log_consistency_p", "consistency", "log_p"),
    ("independence_frac", "independence", "raw"),
]
# Optional noise feature (not in the default set; see the experiment in the model card).
SECONDARY_NEG: tuple[str, str, str] = ("secondary_neg_sigma", "secondary", "neg_clip:10")

FLAG_GROUPS: dict[str, list[str]] = {
    "no_epochs": [
        "odd_even_sigma",
        "log_consistency_p",
        "edges_dumps_frac",
        "secondary_sigma",
        "tau_frac",
    ],
    "no_star": ["log_radius_rearth", "abs_log_duration_ratio"],
}

# Schema 1 (signed duration ratio, signed secondary, one flag per feature). Inference only.
LEGACY_FEATURES_V1: list[tuple[str, str, str]] = [
    ("log_sde", "sde", "log"),
    ("log_snr", "snr", "log"),
    ("log_n_transits", "n_transits", "log"),
    ("odd_even_sigma", "odd_even", "clip:-10:10"),
    ("secondary_sigma", "secondary", "clip:-10:10"),
    ("secondary_scan_sigma", "secondary_scan", "clip:-10:10"),
    ("tau_frac", "shape", "raw"),
    ("log_radius_rearth", "radius", "log"),
    ("log_duration_ratio", "duration", "log"),
    ("centroid_offset_px", "centroid", "clip:-10:10"),
    ("edges_dumps_frac", "edges_dumps", "raw"),
    ("log_consistency_p", "consistency", "log_p"),
    ("independence_frac", "independence", "raw"),
]


# ---------------------------------------------------------------- features


def _transform(v: float | None, how: str) -> float:
    if v is None:
        return float("nan")
    try:
        v = float(v)
    except (TypeError, ValueError):
        return float("nan")
    if not math.isfinite(v):
        return float("nan")
    kind, *args = how.split(":")
    if kind == "log":
        return math.log10(max(v, 1e-3))
    if kind == "log_p":
        return math.log10(max(v, 1e-12))
    if kind == "abs_log":
        return abs(math.log10(max(v, 1e-3)))
    if kind == "clip":
        lo, hi = float(args[0]), float(args[1])
        return max(lo, min(hi, v))
    if kind == "neg_clip":
        return min(float(args[0]), max(0.0, -v))
    if kind == "floor":
        return max(float(args[0]), v)
    return v


def features_from_tests(
    tests: list[dict], spec: list[tuple[str, str, str]] | None = None
) -> dict[str, float]:
    """Feature values (NaN when the test has no value) from vetting test rows."""
    spec = FEATURES if spec is None else spec
    by = {t["name"]: t for t in tests}
    return {name: _transform(by.get(test, {}).get("value"), how) for name, test, how in spec}


def feature_frame(
    tests_json: pd.Series | list[str], spec: list[tuple[str, str, str]] | None = None
) -> pd.DataFrame:
    """One row of features per tests_json string."""
    spec = FEATURES if spec is None else spec
    rows = [features_from_tests(json.loads(t or "[]"), spec) for t in tests_json]
    return pd.DataFrame(rows, columns=[s[0] for s in spec])


# ---------------------------------------------------------------- design matrix


def fit_design(
    F: pd.DataFrame,
    spec: list[tuple[str, str, str]],
    flag_groups: dict[str, list[str]] | None = None,
    min_flag_count: int = MIN_FLAG_COUNT,
) -> dict:
    """Medians, kept missing-flag groups and standardization (continuous columns only)."""
    flag_groups = FLAG_GROUPS if flag_groups is None else flag_groups
    cont = [s[0] for s in spec]
    medians = {c: float(np.nanmedian(F[c])) if F[c].notna().any() else 0.0 for c in cont}
    flags: dict[str, list[str]] = {}
    for name, bases in flag_groups.items():
        bases = [b for b in bases if b in cont]
        if not bases:
            continue
        col = F[bases].isna().any(axis=1)
        if int(col.sum()) >= min_flag_count and int((~col).sum()) >= min_flag_count:
            flags[name] = bases
    design = {"continuous": cont, "medians": medians, "flags": flags}
    X = design_matrix(F, design, standardize=False)
    n_c = len(cont)
    mean = np.zeros(X.shape[1])
    scale = np.ones(X.shape[1])
    mean[:n_c] = X[:, :n_c].mean(axis=0)
    sd = X[:, :n_c].std(axis=0)
    scale[:n_c] = np.where(sd > 1e-12, sd, 1.0)
    design |= {"columns": cont + list(flags), "mean": mean.tolist(), "scale": scale.tolist()}
    return design


def design_matrix(F: pd.DataFrame, design: dict, *, standardize: bool = True) -> np.ndarray:
    """Imputed continuous features followed by 0/1 missing flags (flags are not scaled)."""
    cont = F[design["continuous"]].astype(float)
    flags = [
        cont[bases].isna().any(axis=1).to_numpy(dtype=float) for bases in design["flags"].values()
    ]
    filled = cont.fillna(design["medians"]).to_numpy(dtype=float)
    X = np.column_stack([filled, *flags]) if flags else filled
    if standardize:
        X = (X - np.asarray(design["mean"])) / np.asarray(design["scale"])
    return X


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -50.0, 50.0)))


def _logit(p: float) -> float:
    p = min(max(float(p), 1e-12), 1 - 1e-12)
    return math.log(p / (1 - p))


# ---------------------------------------------------------------- fitting


def _fit_lr(X: np.ndarray, y: np.ndarray, C: float, seed: int):
    from sklearn.linear_model import LogisticRegression

    # Unweighted on purpose: the output must reflect the training class mix (train_prior).
    return LogisticRegression(C=C, max_iter=5000, random_state=seed).fit(X, y)


def _fit_fold(
    F: pd.DataFrame,
    y: np.ndarray,
    C: float,
    seed: int,
    spec: list[tuple[str, str, str]],
    flag_groups: dict[str, list[str]],
    min_flag_count: int,
):
    design = fit_design(F, spec, flag_groups, min_flag_count)
    lr = _fit_lr(design_matrix(F, design), y, C, seed)
    return design, lr


def _folds(n_splits: int, seed: int):
    from sklearn.model_selection import GroupKFold

    return GroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)


def select_C(
    F: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    *,
    grid: tuple[float, ...] = C_GRID,
    n_splits: int = 5,
    seed: int = 0,
    spec: list[tuple[str, str, str]] | None = None,
    flag_groups: dict[str, list[str]] | None = None,
    min_flag_count: int = MIN_FLAG_COUNT,
) -> tuple[float, dict[str, float]]:
    """C with the lowest mean out-of-fold log-loss (GroupKFold by TIC)."""
    from sklearn.metrics import log_loss

    spec = FEATURES if spec is None else spec
    flag_groups = FLAG_GROUPS if flag_groups is None else flag_groups
    n_splits = min(n_splits, len(np.unique(groups)))
    losses: dict[str, float] = {}
    for C in grid:
        oof = np.zeros(len(y))
        for tr, te in _folds(n_splits, seed).split(F, y, groups):
            design, lr = _fit_fold(F.iloc[tr], y[tr], C, seed, spec, flag_groups, min_flag_count)
            oof[te] = lr.predict_proba(design_matrix(F.iloc[te], design))[:, 1]
        losses[str(C)] = float(log_loss(y, np.clip(oof, 1e-9, 1 - 1e-9), labels=[0, 1]))
    best = min(grid, key=lambda c: losses[str(c)])
    return float(best), losses


def _platt(z: np.ndarray, y: np.ndarray) -> dict[str, float]:
    from sklearn.linear_model import LogisticRegression

    lr = LogisticRegression(C=1e6, max_iter=5000).fit(z.reshape(-1, 1), y)
    return {"a": float(lr.coef_[0][0]), "b": float(lr.intercept_[0])}


def cross_validate(
    df: pd.DataFrame,
    *,
    C: float | None = None,
    n_splits: int = 5,
    seed: int = 0,
    grid: tuple[float, ...] = C_GRID,
    spec: list[tuple[str, str, str]] | None = None,
    flag_groups: dict[str, list[str]] | None = None,
    min_flag_count: int = MIN_FLAG_COUNT,
    platt: dict[str, float] | None = None,
) -> dict:
    """Out-of-fold logits and Platt-calibrated probabilities, grouped by TIC.

    C=None runs nested CV (inner grid search per outer fold). ``platt`` given applies those
    parameters; otherwise Platt is fitted on the out-of-fold logits.
    """
    spec = FEATURES if spec is None else spec
    flag_groups = FLAG_GROUPS if flag_groups is None else flag_groups
    F = df[[s[0] for s in spec]]
    y = df["label"].to_numpy(dtype=int)
    groups = df["tic_id"].to_numpy()
    n_splits = min(n_splits, len(np.unique(groups)))
    oof_logit = np.zeros(len(df))
    fold_C: list[float] = []
    for tr, te in _folds(n_splits, seed).split(F, y, groups):
        c = C
        if c is None:
            c, _ = select_C(
                F.iloc[tr],
                y[tr],
                groups[tr],
                grid=grid,
                n_splits=max(2, n_splits - 1),
                seed=seed,
                spec=spec,
                flag_groups=flag_groups,
                min_flag_count=min_flag_count,
            )
        fold_C.append(float(c))
        design, lr = _fit_fold(F.iloc[tr], y[tr], c, seed, spec, flag_groups, min_flag_count)
        oof_logit[te] = lr.decision_function(design_matrix(F.iloc[te], design))
    cal = platt or _platt(oof_logit, y)
    oof = _sigmoid(cal["a"] * oof_logit + cal["b"])
    return {
        "oof_logit": oof_logit,
        "oof_raw": _sigmoid(oof_logit),
        "oof": oof,
        "platt": cal,
        "fold_C": fold_C,
        "metrics": metrics(df, oof, raw=_sigmoid(oof_logit)),
    }


# ---------------------------------------------------------------- metrics and operating points


def _ece(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    bins = np.minimum((p * n_bins).astype(int), n_bins - 1)
    err = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            err += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(err)


def metrics(df: pd.DataFrame, p: np.ndarray, *, raw: np.ndarray | None = None) -> dict:
    """Discrimination and calibration, plus the deterministic score as a baseline."""
    from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

    y = df["label"].to_numpy(dtype=int)
    out: dict = {"n": int(len(y)), "n_planets": int(y.sum()), "n_negatives": int((1 - y).sum())}
    if 0 < y.sum() < len(y):
        out |= {
            "roc_auc_model": float(roc_auc_score(y, p)),
            "pr_auc_model": float(average_precision_score(y, p)),
            "brier_model": float(brier_score_loss(y, p)),
            "log_loss_model": float(log_loss(y, np.clip(p, 1e-9, 1 - 1e-9), labels=[0, 1])),
            "ece_model": _ece(y, p),
        }
        if raw is not None:
            out["brier_uncalibrated"] = float(brier_score_loss(y, raw))
            out["ece_uncalibrated"] = _ece(y, raw)
        if "score" in df and df["score"].notna().all():
            s = df["score"].to_numpy(dtype=float)
            out["roc_auc_score"] = float(roc_auc_score(y, s))
            out["pr_auc_score"] = float(average_precision_score(y, s))
    return out


def _cut_for_recall(pos: np.ndarray, recall: float) -> float:
    """Largest threshold t with mean(pos >= t) >= recall."""
    pos = np.sort(pos)
    k = int(math.floor((1.0 - recall) * len(pos) + 1e-9))
    return float(pos[min(k, len(pos) - 1)])


def _cut_for_fpr(neg: np.ndarray, fpr: float) -> float:
    """Smallest threshold t with mean(neg >= t) <= fpr."""
    neg = np.sort(neg)[::-1]
    m = int(math.floor(fpr * len(neg) + 1e-9))
    if m >= len(neg):
        return 0.0
    return float(np.nextafter(neg[m], np.inf))


def operating_points(
    df: pd.DataFrame,
    p: np.ndarray,
    *,
    p2_recall: float = 0.90,
    p1_recall: float = 0.70,
    p1_fpr_max: float = 0.01,
) -> dict:
    """P2/P1 cuts on out-of-fold p_rank.

    - p2_cut: keeps >= p2_recall of KNOWN_PLANET. Below it a failed-vetting signal is not
      rescued to P2.
    - p1_cut: the lowest cut with out-of-fold FPR <= p1_fpr_max on all negatives, but never
      above the cut that keeps p1_recall of the planets: the ML only demotes, so recall wins
      when both targets cannot be met (the achieved FPR is recorded). Never below p2_cut.
    """
    y = df["label"].to_numpy(dtype=int)
    pos, neg = p[y == 1], p[y == 0]
    p2 = _cut_for_recall(pos, p2_recall)
    p1 = min(_cut_for_fpr(neg, p1_fpr_max), _cut_for_recall(pos, p1_recall))
    p1 = max(p1, p2)
    out: dict = {
        "p2_cut": p2,
        "p1_cut": p1,
        "targets": {"p2_recall": p2_recall, "p1_recall": p1_recall, "p1_fpr_max": p1_fpr_max},
    }
    out |= recall_at_cuts(df, p, {"p2_cut": p2, "p1_cut": p1})
    return out


def recall_at_cuts(df: pd.DataFrame, p: np.ndarray, cuts: dict) -> dict:
    """Recall on KNOWN_PLANET and pass rate per negative source at the P2 and P1 cuts."""
    y = df["label"].to_numpy(dtype=int)
    out: dict = {"n_planets": int((y == 1).sum())}
    for key in ("p2", "p1"):
        cut = cuts[f"{key}_cut"]
        out[f"recall_{key}"] = float((p[y == 1] >= cut).mean()) if (y == 1).any() else None
        out[f"fpr_{key}"] = float((p[y == 0] >= cut).mean()) if (y == 0).any() else None
    if "source" in df:
        by: dict = {}
        for src, idx in df.groupby("source").indices.items():
            ps = p[idx]
            by[str(src)] = {
                "n": int(len(idx)),
                "label": int(y[idx[0]]),
                "mean_p": float(ps.mean()),
                "rate_p2": float((ps >= cuts["p2_cut"]).mean()),
                "rate_p1": float((ps >= cuts["p1_cut"]).mean()),
            }
        out["by_source"] = by
    return out


# ---------------------------------------------------------------- training


def dataset_hash(df: pd.DataFrame, spec: list[tuple[str, str, str]] | None = None) -> str:
    """sha256 of the training table (TIC, label, source, features), order-independent."""
    spec = FEATURES if spec is None else spec
    cols = ["tic_id", "label"] + (["source"] if "source" in df else []) + [s[0] for s in spec]
    cols = [c for c in cols if c in df]
    t = df[cols].copy()
    for c in t.select_dtypes("number").columns:
        t[c] = t[c].astype(float).round(9)
    t = t.sort_values(cols).reset_index(drop=True)
    return hashlib.sha256(t.to_csv(index=False).encode()).hexdigest()


def _code_version() -> str:
    try:
        from planethunter.pipeline import pipeline_version

        return pipeline_version()
    except Exception:
        from planethunter import __version__

        return f"{__version__}+unknown"


def train(
    df: pd.DataFrame,
    *,
    C: float | None = None,
    seed: int = 0,
    n_splits: int = 5,
    grid: tuple[float, ...] = C_GRID,
    spec: list[tuple[str, str, str]] | None = None,
    flag_groups: dict[str, list[str]] | None = None,
    min_flag_count: int = MIN_FLAG_COUNT,
    p2_recall: float = 0.90,
    p1_recall: float = 0.70,
    p1_fpr_max: float = 0.01,
    provenance: dict | None = None,
    sev_cfg=None,
) -> dict:
    """Fit the final model and return the schema-2 JSON dict (with provenance and metrics).

    C=None: chosen on ``grid`` by grouped-CV log-loss on all data; the reported metrics and
    the operating points come from nested CV (outer folds never see the inner choice).
    """
    import sklearn

    spec = FEATURES if spec is None else spec
    flag_groups = FLAG_GROUPS if flag_groups is None else flag_groups
    F = df[[s[0] for s in spec]]
    y = df["label"].to_numpy(dtype=int)
    groups = df["tic_id"].to_numpy()
    cv = cross_validate(
        df,
        C=C,
        n_splits=n_splits,
        seed=seed,
        grid=grid,
        spec=spec,
        flag_groups=flag_groups,
        min_flag_count=min_flag_count,
    )
    if C is None:
        C_final, losses = select_C(
            F,
            y,
            groups,
            grid=grid,
            n_splits=n_splits,
            seed=seed,
            spec=spec,
            flag_groups=flag_groups,
            min_flag_count=min_flag_count,
        )
        c_sel = {
            "method": f"grid, GroupKFold({n_splits}) by TIC, mean log-loss",
            "grid": list(grid),
            "cv_log_loss": losses,
            "nested_outer_fold_C": cv["fold_C"],
        }
    else:
        C_final, c_sel = float(C), {"method": "fixed by caller", "grid": [float(C)]}
    design, lr = _fit_fold(F, y, C_final, seed, spec, flag_groups, min_flag_count)
    ops = operating_points(
        df, cv["oof"], p2_recall=p2_recall, p1_recall=p1_recall, p1_fpr_max=p1_fpr_max
    )
    created = datetime.now(UTC)
    dhash = dataset_hash(df, spec)
    src_counts = (
        {str(k): int(v) for k, v in df["source"].value_counts().items()} if "source" in df else {}
    )
    model = {
        "schema": MODEL_SCHEMA,
        "model_version": f"lr2-{created:%Y%m%dT%H%M%SZ}-{dhash[:8]}",
        "created_at": created.isoformat(timespec="seconds"),
        "code_version": _code_version(),
        "sklearn_version": sklearn.__version__,
        "seed": seed,
        "C": C_final,
        "C_selection": c_sel,
        "class_weight": None,
        "feature_spec": [list(s) for s in spec],
        "features": [s[0] for s in spec],
        "design": design,
        "coef": lr.coef_[0].tolist(),
        "intercept": float(lr.intercept_[0]),
        "platt": cv["platt"],
        "train_prior": float(y.mean()),
        "operating_points": ops,
        "metrics_oof": cv["metrics"],
        "dataset": {
            "hash": dhash,
            "n": int(len(df)),
            "n_planets": int(y.sum()),
            "n_negatives": int((1 - y).sum()),
            "n_tic": int(len(np.unique(groups))),
            "sources": src_counts,
        },
    }
    if provenance:
        model["dataset"] |= provenance
    if {"verdict", "score"} <= set(df.columns) and df["score"].notna().all():
        model["severity_recall_oof"] = severity_recall_vs_baseline(df, cv["oof"], ops, sev_cfg)
    return model


# ---------------------------------------------------------------- persistence and inference


def save_model(model: dict, root: Path, path: Path | None = None) -> Path:
    path = path or root / MODEL_PATH_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return path


def load_model(root: Path, path: Path | None = None) -> dict | None:
    path = path or root / MODEL_PATH_REL
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def model_version(model: dict | None) -> str | None:
    if not model:
        return None
    return model.get("model_version") or f"lr1-{model.get('trained_at', 'unknown')}"


def model_cuts(model: dict | None, p1_fallback: float = 0.8, p2_fallback: float = 0.5) -> dict:
    """P1/P2 operating points of the model; fallbacks for schema 1 or no model."""
    ops = (model or {}).get("operating_points") or {}
    return {
        "p1_cut": float(ops.get("p1_cut", p1_fallback)),
        "p2_cut": float(ops.get("p2_cut", p2_fallback)),
    }


def train_prior(model: dict | None) -> float:
    """Planet fraction the model's probability refers to (schema 1 was balanced: 0.5)."""
    return float((model or {}).get("train_prior", 0.5))


def p_abs(model: dict | None, p_rank: float | None, new_prior: float) -> float | None:
    """Prior-corrected probability for display: logit shift from train_prior to new_prior."""
    if model is None or p_rank is None or not math.isfinite(float(p_rank)):
        return None
    z = _logit(p_rank) + _logit(new_prior) - _logit(train_prior(model))
    return float(_sigmoid(z))


def _predict_v1(model: dict, tests: list[dict]) -> float:
    f = features_from_tests(tests, LEGACY_FEATURES_V1)
    x = []
    for col in model["design_columns"]:
        if col.endswith("_missing"):
            x.append(0.0 if math.isfinite(f[col[: -len("_missing")]]) else 1.0)
        else:
            v = f[col]
            x.append(v if math.isfinite(v) else model["medians"][col])
    z = (np.array(x) - np.array(model["mean"])) / np.array(model["scale"])
    return float(_sigmoid(float(np.dot(z, model["coef"]) + model["intercept"])))


def raw_logit(model: dict, tests: list[dict]) -> float:
    """Uncalibrated logit of a schema-2 model (equals sklearn decision_function)."""
    spec = [tuple(s) for s in model["feature_spec"]]
    f = features_from_tests(tests, spec)
    d = model["design"]
    x = [f[c] if math.isfinite(f[c]) else d["medians"][c] for c in d["continuous"]]
    x += [float(any(not math.isfinite(f[b]) for b in bases)) for bases in d["flags"].values()]
    z = (np.asarray(x) - np.asarray(d["mean"])) / np.asarray(d["scale"])
    return float(np.dot(z, model["coef"]) + model["intercept"])


def predict(model: dict, tests: list[dict]) -> float:
    """p_rank = P(planet | basic vetting tests) under the training class mix. Pure numpy."""
    if model.get("schema", 1) < 2:
        return _predict_v1(model, tests)
    cal = model.get("platt") or {"a": 1.0, "b": 0.0}
    return float(_sigmoid(cal["a"] * raw_logit(model, tests) + cal["b"]))


def predict_frame(model: dict, F: pd.DataFrame) -> np.ndarray:
    """Vectorized p_rank for a frame of features (schema 2)."""
    X = design_matrix(F, model["design"])
    z = X @ np.asarray(model["coef"]) + model["intercept"]
    cal = model.get("platt") or {"a": 1.0, "b": 0.0}
    return _sigmoid(cal["a"] * z + cal["b"])


# ---------------------------------------------------------------- recall helpers (QA)


def oof_recall_at_cuts(df: pd.DataFrame, model: dict, *, n_splits: int = 5) -> dict:
    """Out-of-fold recall on KNOWN_PLANET (label 1) at the model's P2 and P1 cuts.

    Refits with the model's C, features and seed in GroupKFold-by-TIC folds and applies the
    model's Platt parameters, so the cuts are in the same units. ``df`` is a build_dataset()
    table (e.g. the benchmark sector after a rerun).
    """
    spec = [tuple(s) for s in model["feature_spec"]]
    cv = cross_validate(
        df,
        C=float(model["C"]),
        n_splits=n_splits,
        seed=int(model.get("seed", 0)),
        spec=spec,
        flag_groups=model["design"]["flags"],
        min_flag_count=0,
        platt=model.get("platt"),
    )
    return recall_at_cuts(df, cv["oof"], model_cuts(model))


def severity_recall_vs_baseline(df: pd.DataFrame, p: np.ndarray, cuts: dict, sev_cfg=None) -> dict:
    """Severity of known planets (treated as NEW, no deep vetting) with and without the ML.

    Baseline = deterministic score only. By construction the ML cannot lower recall at >= P2
    (it only demotes P1 -> P2 and rescues FAIL -> P2); P1 recall is the price of the demotion.
    Needs `verdict` and `score` columns.
    """
    from planethunter.alerts.severity import severity

    out: dict = {}
    for label, name in ((1, "planets"), (0, "negatives")):
        idx = np.flatnonzero(df["label"].to_numpy() == label)
        sml, sbase = [], []
        for i in idx:
            r = df.iloc[i]
            kw = {"cfg": sev_cfg} if sev_cfg is not None else {}
            sml.append(
                severity(
                    "NEW",
                    r["verdict"],
                    r["score"],
                    p_planet=float(p[i]),
                    p1_cut=cuts["p1_cut"],
                    p2_cut=cuts["p2_cut"],
                    **kw,
                )
            )
            sbase.append(severity("NEW", r["verdict"], r["score"], **kw))
        n = max(len(idx), 1)
        out[name] = {
            "n": int(len(idx)),
            "ge_p2_ml": sum(s != "NONE" for s in sml) / n,
            "ge_p2_baseline": sum(s != "NONE" for s in sbase) / n,
            "p1_ml": sum(s in ("P0", "P1") for s in sml) / n,
            "p1_baseline": sum(s in ("P0", "P1") for s in sbase) / n,
        }
    return out


# ---------------------------------------------------------------- dataset


def default_runs(root: Path) -> tuple[list[str], list[str]]:
    """Latest labeled run per (mode, sector, author) and latest null run per (mode, sector).

    Older runs of the same sector hold features from older code; the latest one wins.
    """
    from planethunter.db.store import connect

    con = connect(root, read_only=True)
    try:
        runs = con.execute(
            """
            SELECT r.run_id, r.mode, r.sector, r.author, r.started_at,
                   EXISTS (SELECT 1 FROM signals s JOIN crossmatch c USING (signal_id)
                           WHERE s.run_id = r.run_id AND c.match_class IN (?, ?)) AS labeled
            FROM search_runs r
            """,
            list(LABELED_CLASSES),
        ).df()
    finally:
        con.close()
    if runs.empty:
        return [], []
    runs["started_at"] = runs["started_at"].fillna(pd.Timestamp(0))
    runs = runs.sort_values(["started_at", "run_id"])
    key = ["mode", "sector", "author"]
    is_null = runs["mode"].isin(NULL_MODES)
    labeled = runs[~is_null & runs["labeled"]].drop_duplicates(key, keep="last")
    null = runs[is_null].drop_duplicates(key, keep="last")
    return sorted(labeled["run_id"]), sorted(null["run_id"])


def _source(row) -> str:
    if row["kind"] != "real":
        return str(row["kind"])
    if row["match_class"] == "KNOWN_FP":
        return "eb_catalog" if row["matched_source"] == "eb_catalog" else "tfopwg_fp"
    return str(row["matched_source"] or "unknown")


def null_vetting_supported() -> bool:
    """True if basic vetting re-applies the null transform (preprocess.apply_null, from
    search_runs.mode) to a null-run target before vetting it. Without that, null-run signals
    would be vetted on the original light curve and their features would be meaningless."""
    import inspect

    try:
        from planethunter import pipeline

        return "apply_null" in inspect.getsource(pipeline._vet_target)
    except (OSError, TypeError, AttributeError, ImportError):
        return False


def build_dataset(
    root: Path,
    cfg,
    runs: list[str],
    *,
    null_runs: list[str] | None = None,
    recompute: bool = False,
    workers: int = 4,
    positive_alias: str = "any",
    allow_unverified_null: bool = False,
) -> pd.DataFrame:
    """Training table: one row per signal with label, source, score, verdict and features.

    - Labeled runs: KNOWN_PLANET (1) and KNOWN_FP (0) after crossmatch.
    - Null runs: every vetted signal (SDE >= vetting.sde_min) is a false alarm (0). Refused
      (RuntimeError) unless vetting is null-aware (null_vetting_supported()), because the
      features must come from the same inverted/scrambled light curve the search saw.
    - Features come from the stored vetting.tests_json; runs without vetting rows, or all
      runs with recompute=True, are re-vetted with the current code (no DB writes).
    - positive_alias="1": keep only planets matched at alias 1 (drops 1/2, 2, unknown).
    - The same signal in several runs counts once (latest run wins). Read-only on the DB.
    """
    from planethunter.db.store import connect

    null_runs = list(null_runs or [])
    if null_runs and not (allow_unverified_null or null_vetting_supported()):
        raise RuntimeError(
            "basic vetting does not re-apply the null transform (pipeline._vet_target has no "
            "apply_null), so null-run features would come from the original light curves. "
            "Train without null runs (--null-runs none) until vetting is null-aware."
        )
    all_runs = list(runs) + null_runs
    if not all_runs:
        raise ValueError("no runs to build a dataset from")
    con = connect(root, read_only=True)
    try:
        ph = ",".join("?" * len(all_runs))
        meta = con.execute(
            f"""
            SELECT s.signal_id, s.tic_id, s.sectors, s.period_days, s.sde, s.run_id, r.mode,
                   c.match_class, c.matched_source, c.alias
            FROM signals s
            LEFT JOIN crossmatch c USING (signal_id)
            LEFT JOIN search_runs r ON r.run_id = s.run_id
            WHERE s.run_id IN ({ph}) AND s.sde >= ?
            """,
            [*all_runs, cfg.vetting.sde_min],
        ).df()
        stored = con.execute(
            f"""
            SELECT v.signal_id, s.run_id, v.score, v.verdict, v.tests_json
            FROM vetting v JOIN signals s USING (signal_id) WHERE s.run_id IN ({ph})
            """,
            all_runs,
        ).df()
    finally:
        con.close()
    have = set(stored["run_id"])
    redo = [r for r in all_runs if recompute or r not in have]
    vet = stored[~stored["run_id"].isin(redo)].drop(columns=["run_id"])
    if redo:
        from planethunter.pipeline import run_vetting

        fresh = [run_vetting(root, cfg, r, write=False, workers=workers) for r in redo]
        fresh = [f[["signal_id", "score", "verdict", "tests_json"]] for f in fresh if len(f)]
        vet = pd.concat([vet, *fresh], ignore_index=True)
    df = meta.merge(vet, on="signal_id", how="inner")
    df["kind"] = np.where(df["run_id"].isin(null_runs), df["mode"].fillna("null"), "real")
    real = df["kind"] == "real"
    df = df[~real | df["match_class"].isin(LABELED_CLASSES)].copy()
    if positive_alias == "1":
        drop = (df["kind"] == "real") & (df["match_class"] == "KNOWN_PLANET")
        df = df[~drop | (df["alias"].astype(str) == "1")].copy()
    df["label"] = ((df["kind"] == "real") & (df["match_class"] == "KNOWN_PLANET")).astype(int)
    df["source"] = df.apply(_source, axis=1)
    df["key"] = (
        df["kind"]
        + "|"
        + df["tic_id"].astype(str)
        + "|"
        + df["sectors"].astype(str)
        + "|"
        + df["period_days"].round(2).astype(str)
    )
    df = df.sort_values("run_id").drop_duplicates("key", keep="last").reset_index(drop=True)
    feats = feature_frame(df["tests_json"], [*FEATURES, SECONDARY_NEG])
    keep = ["signal_id", "tic_id", "run_id", "label", "source", "alias", "score", "verdict"]
    return pd.concat([df[keep], feats, df[["tests_json"]]], axis=1)
