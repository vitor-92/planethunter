"""Ranking probability, severity rules, deep-vetting adjustment and the model (schema 2)."""

import json
import math

import numpy as np
import pandas as pd
import pytest

from planethunter.alerts.severity import severity
from planethunter.config import Config, SeverityConfig
from planethunter.db.store import connect, insert_df, upsert_df
from planethunter.ml.calibrate import (
    FEATURES,
    FLAG_GROUPS,
    _fit_fold,
    build_dataset,
    design_matrix,
    feature_frame,
    load_model,
    model_cuts,
    oof_recall_at_cuts,
    operating_points,
    p_abs,
    predict,
    predict_frame,
    raw_logit,
    save_model,
    severity_recall_vs_baseline,
    train,
)
from planethunter.pipeline import (
    _deep_done,
    _outside_validation_region,
    _p_final,
    _rp_rearth,
    candidate_table,
    promote_candidates,
)

REGION = dict(nfpp=1e-4, rp_rearth=2.0, snr=20.0, two_min_cadence=True)
CUTS = dict(p1_cut=0.85, p2_cut=0.6)


# ---------------------------------------------------------------- severity


def test_ml_only_lowers_priority():
    # Audit A2: a low deterministic score is never promoted by a high p_rank.
    assert severity("NEW", "PASS_BASIC", 0.55, deep_done=True, fpp=0.01, p_planet=0.99) not in (
        "P0",
        "P1",
    )
    assert severity("NEW", "PASS_BASIC", 0.55, p_planet=0.99, **CUTS) == "P2"
    # Both the score and p_rank must clear their cuts for P1.
    assert severity("NEW", "PASS_BASIC", 0.9, p_planet=0.9, **CUTS) == "P1"
    assert severity("NEW", "PASS_BASIC", 0.9, p_planet=0.8, **CUTS) == "P2"
    assert severity("NEW", "PASS_BASIC", 0.9) == "P1"  # no model: deterministic only
    # The ML never vetoes on its own: passed deterministic vetting, low p -> lower priority.
    assert severity("NEW", "PASS_BASIC", 1.0, p_planet=0.01, **CUTS) == "P2"
    # Failed vetting (no veto): rescued at most to P2, only above the P2 cut.
    assert severity("NEW", "FAIL", 0.4, p_planet=0.99, **CUTS) == "P2"
    assert severity("NEW", "FAIL", 0.4, deep_done=True, fpp=0.01, p_planet=0.99, **REGION) == "P2"
    assert severity("NEW", "FAIL", 0.4, p_planet=0.5, **CUTS) == "NONE"
    assert severity("NEW", "FAIL", 0.4) == "NONE"
    assert severity("NEW", "FAIL", 0.0, p_planet=0.99, **CUTS) == "NONE"  # a veto eliminates
    assert severity("KNOWN_TOI", "PASS_BASIC", 1.0, p_planet=0.99) == "NONE"
    # Fallback cuts (schema-1 model) come from the config.
    assert severity("NEW", "PASS_BASIC", 0.9, p_planet=0.79) == "P2"


def test_p0_requires_deep_vetting_and_validation_region():
    base = dict(deep_done=True, fpp=0.05, p_planet=0.95, **CUTS)
    assert severity("NEW", "PASS_BASIC", 0.9, **base, **REGION) == "P0"
    for change in (
        {"nfpp": 1.6e-3},  # signal 4482: above the 1e-3 validation cut
        {"rp_rearth": 9.0},
        {"rp_rearth": None},
        {"snr": 8.0},  # signal 4482: SNR 8
        {"two_min_cadence": False},  # 30-min FFI
        {"nfpp": None},
    ):
        assert severity("NEW", "PASS_BASIC", 0.9, **base, **(REGION | change)) == "P1", change
    assert severity("NEW", "PASS_BASIC", 0.9, **(base | {"deep_done": False}), **REGION) == "P1"
    assert severity("NEW", "PASS_BASIC", 0.9, **(base | {"fpp": 0.2}), **REGION) == "P1"
    assert (
        severity("NEW", "PASS_BASIC", 0.9, **base, **REGION, outside_validation_region=True) == "P1"
    )
    # NFPP > 0.1: likely nearby false positive (signal 4055, NFPP 0.24) -> ceiling P2.
    assert severity("NEW", "PASS_BASIC", 0.9, **base, **(REGION | {"nfpp": 0.24})) == "P2"
    # Thresholds come from the config.
    loose = SeverityConfig(p0_snr_min=5.0, p0_nfpp_max=0.01)
    assert (
        severity(
            "NEW", "PASS_BASIC", 0.9, **base, **(REGION | {"snr": 8, "nfpp": 1.6e-3}), cfg=loose
        )
        == "P0"
    )


def test_systematics_and_blend_flags():
    ok = dict(p_planet=0.95, **CUTS)
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, epoch_spike_frac=0.2) == "P1"
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, epoch_spike_frac=0.5) == "NONE"
    assert severity("NEW", "FAIL", 0.4, **ok, epoch_spike_frac=1.0) == "NONE"  # no rescue
    assert (
        severity("NEW", "PASS_BASIC", 0.9, **ok, epoch_spike_frac=0.5, epoch_spike_max_frac=0.8)
        == "P1"
    )
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, epoch_spike_frac=float("nan")) == "P1"
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, shared_signal_role="duplicate") == "NONE"
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, shared_signal_role="victim") == "NONE"
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, shared_signal_role="source") == "P2"
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, shared_signal_role=None) == "P1"
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, periodless_known_on_host=True) == "P2"
    full = dict(deep_done=True, fpp=0.01, **REGION)
    assert severity("NEW", "PASS_BASIC", 0.9, **ok, **full, shared_signal_role="source") == "P2"


def test_deep_done_needs_tpf_gaia_and_fpp_passed():
    def tests(tpf=True, gaia=True, fpp=True):
        return [
            {"name": "tpf_difference_image", "passed": tpf, "veto": False},
            {"name": "gaia_neighbors", "passed": gaia, "veto": False},
            {"name": "fpp_triceratops", "passed": fpp, "veto": False},
        ]

    assert _deep_done(tests(), "")
    assert not _deep_done(tests(gaia=None), "")  # signal 3747: gaia_neighbors = None
    assert not _deep_done(tests(tpf=None), "")
    assert not _deep_done(tests(fpp=None), "")
    assert not _deep_done(tests(fpp=False), "")
    assert not _deep_done(tests(), "fpp_triceratops")
    assert not _deep_done(tests()[:2], "")


def test_validation_region_flag_and_radius():
    fpp = {"name": "fpp_triceratops", "passed": True, "note": "FPP 0.01"}
    assert not _outside_validation_region([fpp])
    assert _outside_validation_region([fpp | {"note": "FPP 0.01; outside_validation_region"}])
    assert _outside_validation_region([fpp | {"validation_region": False}])
    assert not _outside_validation_region([fpp | {"validation_region": True, "note": "x"}])
    assert not _outside_validation_region([])
    # Contract with deep vetting (vetting/deep.py fpp_test): extra.in_validation_region wins.
    assert _outside_validation_region([fpp | {"extra": {"in_validation_region": False}}])
    inside = fpp | {"extra": {"in_validation_region": True}, "note": "outside_validation_region"}
    assert not _outside_validation_region([inside])
    assert _rp_rearth(10000, None, 1.0) == pytest.approx(0.1 * 109.076)
    assert _rp_rearth(10000, 0.2, 1.0) == pytest.approx(0.2 * 109.076)  # the larger wins
    assert _rp_rearth(10000, 0.2, None) is None


def test_p_final_penalizes_in_odds_space_and_never_raises():
    cfg = Config()
    tests = [
        {"name": "odd_even", "passed": False, "veto": False},  # basic test: ignored here
        {"name": "other_sectors", "passed": False, "veto": False},
    ]
    w = cfg.vetting.weights["other_sectors"]
    z = math.log(0.9 / 0.1) + math.log(w)
    assert _p_final(0.9, json.dumps(tests), cfg) == pytest.approx(1 / (1 + math.exp(-z)))
    for p in (0.0, 0.01, 0.5, 0.99, 1.0):
        assert _p_final(p, json.dumps(tests), cfg) <= p
    assert _p_final(0.7, json.dumps(tests[:1]), cfg) == 0.7
    tests[1]["veto"] = True
    assert _p_final(0.9, json.dumps(tests), cfg) == 0.0
    assert _p_final(None, "[]", cfg) is None


# ---------------------------------------------------------------- model


def _synthetic(n=300, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, n)
    rows = []
    for i, lab in enumerate(y):
        row = {name: rng.normal() for name, _, _ in FEATURES}
        row["log_radius_rearth"] = rng.normal(0.4 if lab else 1.3, 0.3)  # FPs are larger
        row["secondary_sigma"] = max(0.0, rng.normal(0.5 if lab else 4.0, 1.0))
        if rng.random() < 0.15:
            row["odd_even_sigma"] = np.nan  # few epochs
        src = "archive_pscomppars" if lab else ("eb_catalog" if i % 3 else "null-inverted")
        rows.append(
            {
                "signal_id": i,
                "tic_id": i // 2,
                "label": int(lab),
                "source": src,
                "score": float(np.clip(rng.normal(0.8 if lab else 0.4, 0.2), 0.05, 1)),
                "verdict": "PASS_BASIC" if rng.random() < (0.8 if lab else 0.2) else "FAIL",
                **row,
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def trained():
    df = _synthetic()
    return df, train(df, seed=0, grid=(0.1, 1.0), n_splits=4, provenance={"runs": ["toy"]})


def test_model_learns_with_provenance_and_operating_points(trained):
    df, model = trained
    m = model["metrics_oof"]
    assert m["roc_auc_model"] > 0.9
    assert model["schema"] == 2 and model["class_weight"] is None
    for key in ("model_version", "created_at", "code_version", "sklearn_version", "seed", "C"):
        assert model[key] is not None
    assert model["C"] in (0.1, 1.0) and model["C_selection"]["cv_log_loss"]
    assert len(model["dataset"]["hash"]) == 64 and model["dataset"]["runs"] == ["toy"]
    assert 0 < model["train_prior"] < 1
    ops = model["operating_points"]
    assert ops["recall_p2"] >= 0.9 and ops["recall_p1"] >= 0.7 and ops["p1_cut"] >= ops["p2_cut"]
    assert set(ops["by_source"]) == {"archive_pscomppars", "eb_catalog", "null-inverted"}
    assert model_cuts(model) == {"p1_cut": ops["p1_cut"], "p2_cut": ops["p2_cut"]}
    # Binary flags are not standardized; the merged flag replaces per-feature flags.
    d = model["design"]
    assert list(d["flags"]) == ["no_epochs"]
    i = d["columns"].index("no_epochs")
    assert d["mean"][i] == 0.0 and d["scale"][i] == 1.0
    # Recall at >= P2 can never drop below the deterministic baseline (ML only demotes/rescues).
    rec = model["severity_recall_oof"]["planets"]
    assert rec["ge_p2_ml"] >= rec["ge_p2_baseline"]


def test_saved_model_loads_and_predict_equals_sklearn(trained, tmp_path):
    df, model = trained
    path = save_model(model, tmp_path)
    loaded = load_model(tmp_path)
    assert path.exists() and loaded["model_version"] == model["model_version"]
    # Same data, C and seed: the refit equals the stored coefficients.
    F = df[[s[0] for s in FEATURES]]
    y = df["label"].to_numpy()
    design, lr = _fit_fold(F, y, loaded["C"], loaded["seed"], FEATURES, FLAG_GROUPS, 20)
    np.testing.assert_allclose(lr.coef_[0], loaded["coef"], rtol=1e-10, atol=1e-12)
    # Toy vetting rows (one with missing tests: imputation + flag) through both paths.
    rng = np.random.default_rng(5)
    rows = [
        [{"name": t, "value": float(rng.uniform(0.01, 20))} for _, t, _ in FEATURES]
        for _ in range(30)
    ]
    rows[0] = rows[0][:3]
    Fx = feature_frame([json.dumps(r) for r in rows])
    sk = lr.decision_function(design_matrix(Fx, design))
    ours = np.array([raw_logit(loaded, r) for r in rows])
    np.testing.assert_allclose(ours, sk, rtol=1e-9, atol=1e-9)
    a, b = loaded["platt"]["a"], loaded["platt"]["b"]
    p_one = np.array([predict(loaded, r) for r in rows])
    np.testing.assert_allclose(p_one, 1 / (1 + np.exp(-(a * sk + b))), rtol=1e-9)
    np.testing.assert_allclose(predict_frame(loaded, Fx), p_one, rtol=1e-12)


def test_legacy_schema1_model_still_predicts():
    cols = [
        "log_sde",
        "log_radius_rearth",
        "log_duration_ratio",
        "log_radius_rearth_missing",
    ]
    v1 = {
        "version": 1,
        "trained_at": "2026-10-10T01:01:29+00:00",
        "design_columns": cols,
        "medians": {"log_sde": 1.0, "log_radius_rearth": 1.0, "log_duration_ratio": 0.0},
        "mean": [0, 0, 0, 0],
        "scale": [1, 1, 1, 1],
        "coef": [0.0, -1.0, 0.3, 0.0],
        "intercept": 0.0,
    }
    small = [{"name": "radius", "value": 1.0}, {"name": "duration", "value": 1.0}]
    big = [{"name": "radius", "value": 100.0}, {"name": "duration", "value": 1.0}]
    assert predict(v1, small) == pytest.approx(0.5)
    assert predict(v1, big) < 0.2
    assert model_cuts(v1) == {"p1_cut": 0.8, "p2_cut": 0.5}


def test_p_abs_prior_correction():
    model = {"train_prior": 0.5}
    assert p_abs(model, 0.5, 0.05) == pytest.approx(0.05)
    assert p_abs({"train_prior": 0.4}, 0.4, 0.4) == pytest.approx(0.4)
    vals = [p_abs(model, p, 0.05) for p in (0.1, 0.5, 0.9, 0.99)]
    assert vals == sorted(vals) and all(
        v < p for v, p in zip(vals, (0.1, 0.5, 0.9, 0.99), strict=True)
    )
    assert p_abs(None, 0.9, 0.05) is None and p_abs(model, None, 0.05) is None


def test_operating_points_hit_recall_targets():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"label": [1] * 100 + [0] * 400, "source": ["p"] * 100 + ["n"] * 400})
    p = np.r_[rng.beta(5, 2, 100), rng.beta(2, 5, 400)]
    ops = operating_points(df, p, p2_recall=0.9, p1_recall=0.7, p1_fpr_max=0.01)
    assert ops["recall_p2"] >= 0.9 and ops["recall_p1"] >= 0.7
    assert ops["p1_cut"] >= ops["p2_cut"]
    # When 1 % FPR would cost more than 30 % recall, recall wins and the FPR is recorded.
    assert ops["fpr_p1"] > 0.01 or ops["recall_p1"] >= 0.7


def test_recall_helpers(trained):
    df, model = trained
    rec = oof_recall_at_cuts(df, model, n_splits=4)
    assert rec["n_planets"] == int(df["label"].sum())
    assert rec["recall_p2"] >= rec["recall_p1"] and rec["recall_p2"] > 0.8
    p = predict_frame(model, df)
    sev = severity_recall_vs_baseline(df, p, model_cuts(model))
    assert sev["planets"]["ge_p2_ml"] >= sev["planets"]["ge_p2_baseline"]
    assert sev["planets"]["p1_ml"] <= sev["planets"]["p1_baseline"]  # only demotes


# ---------------------------------------------------------------- DB integration


def _tests_json(radius=2.0, secondary=0.0, sde=12.0):
    rows = [
        {"name": "sde", "value": sde, "passed": True, "veto": False},
        {"name": "snr", "value": 20.0, "passed": True, "veto": False},
        {"name": "radius", "value": radius, "passed": True, "veto": False},
        {"name": "secondary", "value": secondary, "passed": True, "veto": False},
    ]
    return json.dumps(rows)


def _seed_db(root):
    con = connect(root)
    insert_df(
        con,
        "search_runs",
        pd.DataFrame(
            [
                {"run_id": "real", "mode": "single", "sector": 1, "author": "SPOC"},
                {"run_id": "null", "mode": "null-inverted", "sector": 1, "author": "SPOC"},
            ]
        ),
    )
    sig, xm, vet = [], [], []
    cls = ["KNOWN_PLANET", "KNOWN_FP", "NEW", "NEW", "NEW", "KNOWN_TOI"]
    for i, c in enumerate(cls, start=1):
        sig.append(
            {
                "signal_id": i,
                "run_id": "real",
                "tic_id": 100 + i,
                "sectors": "1",
                "author": "SPOC",
                "period_days": 1.0 + i,
                "sde": 12.0,
                "snr": 20.0,
            }
        )
        xm.append({"signal_id": i, "match_class": c, "matched_source": "toi", "alias": "1"})
        vet.append(
            {
                "signal_id": i,
                "verdict": "PASS_BASIC",
                "score": 0.9,
                "deep_pending": "",
                "tests_json": _tests_json(radius=20.0 if c == "KNOWN_FP" else 2.0),
            }
        )
    for j in range(3):  # null run: false alarms
        sid = 10 + j
        sig.append(
            {
                "signal_id": sid,
                "run_id": "null",
                "tic_id": 200 + j,
                "sectors": "1",
                "author": "SPOC",
                "period_days": 3.3,
                "sde": 10.0,
                "snr": 8.0,
            }
        )
        vet.append(
            {
                "signal_id": sid,
                "verdict": "FAIL",
                "score": 0.3,
                "deep_pending": "",
                "tests_json": _tests_json(sde=10.0),
            }
        )
    insert_df(con, "signals", pd.DataFrame(sig))
    insert_df(con, "crossmatch", pd.DataFrame(xm))
    upsert_df(con, "vetting", pd.DataFrame(vet))
    insert_df(
        con, "targets", pd.DataFrame([{"tic_id": 100 + i, "radius_rsun": 1.0} for i in range(1, 7)])
    )
    # Systematics flags on NEW signals 4 and 5 (crossmatch contract).
    con.execute("UPDATE crossmatch SET epoch_spike_frac = 0.8 WHERE signal_id = 4")
    con.execute("UPDATE crossmatch SET shared_signal_role = 'victim' WHERE signal_id = 5")
    con.close()


def test_build_dataset_uses_null_runs_as_negatives(tmp_path, cfg):
    _seed_db(tmp_path)
    df = build_dataset(tmp_path, cfg, ["real"], null_runs=["null"], allow_unverified_null=True)
    assert sorted(df["source"]) == ["null-inverted"] * 3 + ["tfopwg_fp", "toi"]
    assert df.loc[df["source"] == "toi", "label"].tolist() == [1]
    assert df.loc[df["source"] != "toi", "label"].eq(0).all()
    assert "abs_log_duration_ratio" in df and "secondary_neg_sigma" in df


def test_promote_applies_systematics_flags_and_model_cuts(tmp_path, cfg):
    _seed_db(tmp_path)
    out = promote_candidates(tmp_path, cfg, "real")
    sev = dict(zip(out["signal_id"], out["severity"], strict=True))
    assert sev == {3: "P1"}  # 4 = epoch spikes, 5 = victim of a neighbor's signal
    # A model whose P1 cut sits above this signal's p_rank demotes it (never removes it).
    df = _synthetic()
    model = train(df, seed=0, C=1.0, n_splits=3)
    model["operating_points"]["p1_cut"] = 1.01  # above any p_rank
    model["operating_points"]["p2_cut"] = 0.5
    save_model(model, tmp_path)
    out = promote_candidates(tmp_path, cfg, "real")
    assert dict(zip(out["signal_id"], out["severity"], strict=True)) == {3: "P2"}
    con = connect(tmp_path)
    row = con.execute(
        "SELECT p_planet, p_abs, model_version FROM vetting WHERE signal_id = 3"
    ).fetchone()
    con.close()
    assert row[2] == model["model_version"] and 0 <= row[1] <= row[0] <= 1
    table = candidate_table(tmp_path, "real")
    assert {"p_rank", "p_abs", "epoch_spike_frac", "shared_signal_role"} <= set(table.columns)


def test_partial_known_transit_caps_at_p2():
    from planethunter.alerts.severity import severity

    assert severity("NEW", "PASS_BASIC", 1.0, partial_known_transit=True) == "P2"
    assert severity("NEW", "PASS_BASIC", 1.0) == "P1"
