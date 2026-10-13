"""Configuration: versioned thresholds (config/thresholds.yaml) and data paths."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "thresholds.yaml"

MAX_WORKERS_ENV = "PLANETHUNTER_MAX_WORKERS"
NATIVE_THREAD_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMBA_NUM_THREADS",
)


def worker_cap() -> int | None:
    """Global cap on parallel analysis processes from PLANETHUNTER_MAX_WORKERS (None = no cap)."""
    raw = os.environ.get(MAX_WORKERS_ENV, "").strip()
    if not raw:
        return None
    try:
        cap = int(raw)
    except ValueError as exc:
        raise ValueError(f"{MAX_WORKERS_ENV} must be a positive integer, got {raw!r}") from exc
    if cap < 1:
        raise ValueError(f"{MAX_WORKERS_ENV} must be >= 1, got {cap}")
    return cap


def max_workers(requested: int | None, default: int) -> int:
    """Processes for an analysis pool: `requested` (CLI) or `default` (config), capped by
    PLANETHUNTER_MAX_WORKERS. Each process runs one native thread (see limit_native_threads),
    so this is also the number of CPU cores used."""
    n = requested if requested and requested > 0 else default
    cap = worker_cap()
    return max(1, min(n, cap) if cap else n)


def limit_native_threads() -> None:
    """One BLAS/OpenMP thread per process unless the user set these variables. Called before a
    process pool starts: child processes inherit the environment, so N workers use N cores
    instead of N x (threads per BLAS call)."""
    for var in NATIVE_THREAD_VARS:
        os.environ.setdefault(var, "1")


class PreprocessConfig(BaseModel):
    quality_bitmask: str = "default"
    sigma_upper: float = 4.0
    detrend_method: str = "biweight"
    window_length_days: float = 1.0
    fallback_windows_days: list[float] = Field(default_factory=lambda: [0.5, 0.3])
    red_noise_max: float = 1.2
    red_noise_bin_hours: float = 0.0
    break_tolerance_days: float = 0.5
    edge_cutoff_days: float = 0.0
    min_points: int = 500
    min_window_durations: float = 3.0
    signal_mask_width_durations: float = 1.5


class SearchConfig(BaseModel):
    bin_minutes: float = 10.0
    period_min_days: float = 0.2
    period_max_fraction_of_span: float = 0.9
    period_max_days: float = 40.0
    n_transits_min: int = 1
    roche_min_a_rstar: float = 2.0
    oversampling_factor: int = 3
    duration_grid_step: float = 1.1
    limb_darkening: str = "tess"
    max_signals_per_target: int = 3
    sde_keep: float = 7.0
    mask_width_durations: float = 2.0
    min_epoch_coverage: float = 0.5
    segment_gap_days: float = 0.5
    edge_window_days: float = 0.5
    workers: int = 0
    tls_backend: str = "fused-pl"
    null_seed: int = 0

    def n_workers(self) -> int:
        """Pool size: `search.workers` or n_cpus - 1, capped by PLANETHUNTER_MAX_WORKERS."""
        default = self.workers if self.workers > 0 else max(1, (os.cpu_count() or 2) - 1)
        return max_workers(None, default)


class VettingConfig(BaseModel):
    sde_min: float = 9.0
    snr_min: float = 7.1
    snr_pink_min: float = 9.0
    snr_pink_veto: bool = False
    min_transits: int = 2
    max_edge_transit_fraction: float = 0.5
    odd_even_fail_sigma: float = 3.0
    odd_even_veto_sigma: float = 5.0
    secondary_fail_sigma: float = 3.0
    secondary_veto_sigma: float = 5.0
    secondary_veto_ratio: float = 0.1
    halving_max_depth_sigma: float = 3.0
    halving_duration_tol: float = 0.35
    trapezoid_f_scale_sigma: float = 1.0
    rp_rs_max: float = 0.3
    ld_fit_enabled: bool = True
    ld_fit_subexposure_minutes: float = 2.0
    ld_fit_delta_chi2: float = 1.0
    kdr25_max: float = 1.04
    v_shape_max: float = 0.35
    secondary_scan_fail_sigma: float = 5.0
    radius_fail_rearth: float = 22.4
    radius_veto_rearth: float = 33.6
    radius_veto_min_logg: float = 3.5
    duration_ratio_max: float = 1.67
    duration_ratio_min: float = 0.15
    centroid_fail_sigma: float = 3.0
    centroid_max_offset_px: float = 1.0
    centroid_min_transits: int = 3
    centroid_min_tmag: float = 7.0
    centroid_null_epochs: int = 200
    dump_window_days: float = 0.1
    max_dump_transit_fraction: float = 0.5
    transit_consistency_pvalue_min: float = 0.001
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "sde": 0.5,
            "snr": 0.5,
            "n_transits": 0.6,
            "odd_even": 0.4,
            "secondary": 0.4,
            "secondary_scan": 0.5,
            "tpf_difference_image": 0.3,
            "other_sectors": 0.3,
            "simbad_type": 0.5,
            "gaia_eb": 0.4,
            "fpp_triceratops": 0.3,
            "shape": 0.5,
            "radius": 0.3,
            "duration": 0.6,
            "centroid": 0.4,
            "edges_dumps": 0.4,
            "consistency": 0.5,
            "gaia_neighbors": 0.5,
            "snr_pink": 0.5,
            "kdr25_grazing": 0.6,
        }
    )
    unknown_weight: float = 0.95
    unknown_exempt_tests: list[str] = Field(default_factory=lambda: ["snr_pink", "kdr25_grazing"])
    max_soft_fails: int = 1
    uncounted_soft_tests: list[str] = Field(default_factory=lambda: ["snr_pink"])
    hard_fail_tests: list[str] = Field(
        default_factory=lambda: [
            "tpf_difference_image",
            "fpp_triceratops",
            "secondary_scan",
            "shape",
        ]
    )
    mask_weaker_signals: bool = False
    tpf_offset_sigma: float = 3.0
    tpf_max_offset_px: float = 1.0
    psf_sigma_px: float = 0.75
    other_sectors_null_trials: int = 40
    simbad_fail_otypes: list[str] = Field(default_factory=lambda: ["EB*", "SB*", "El*"])
    fpp_enabled: bool = True
    fpp_draws: int = 100_000
    fpp_repeats: int = 3
    fpp_timeout_s: int = 1800
    fpp_max: float = 0.5
    fpp_nfpp_fail: float = 0.1
    fpp_nfpp_veto: float = 0.5
    fpp_validated: float = 0.015
    fpp_nfpp_validated: float = 1e-3
    fpp_validation_max_rp_rearth: float = 8.0
    fpp_validation_min_snr: float = 15.0
    fpp_validation_max_exptime_min: float = 2.0
    deep_workers: int = 4
    pass_score: float = 0.5


class CrossmatchConfig(BaseModel):
    """Crossmatch thresholds. Units: periods in days, angles in arcsec, ages in hours."""

    # Period matching (aliases {1, 2, 1/2, 3, 1/3, 3/2, 2/3}).
    period_rel_tol: float = 0.01  # floor; beyond it a phase check is mandatory
    period_rel_tol_max: float = 0.03  # cap of max(floor, 3 sigma_rel of the candidate)
    phase_tol: float = 0.05  # fraction of the common period grid
    default_period_rel_err: float = 1e-4  # sigma_P / P assumed when a catalog gives none
    # Star matching
    host_radius_arcsec: float = 21.0
    nearby_radius_arcsec: float = 120.0
    # Mirror freshness. Default for live sources (ExoFOP TOI/CTOI, Archive); per-source
    # overrides below; static catalogs only need to be present with the expected version.
    mirror_max_age_hours: float = 48.0
    mirror_max_age_hours_by_source: dict[str, float] = Field(
        default_factory=lambda: {
            "exoplanet_eu": 168.0,
            "k2_pandc": 168.0,
            "koi_cumulative": 720.0,
        }
    )
    static_sources: list[str] = Field(
        default_factory=lambda: [
            "eb_catalog",
            "eb_kostov2025",
            "pub_diamante",
            "pub_dtarps",
            "pub_leo_vetter",
            "pub_exominerpp",
        ]
    )
    # Transit-by-transit matcher (audit A9)
    transit_window_floor_hours: float = 1.0  # floor of the 0.5 * duration half-window
    transit_max_unc_days: float = 0.25  # skip objects whose 3 sigma_prop exceeds this...
    transit_max_unc_frac: float = 0.1  # ...or this fraction of their period
    transit_min_fraction: float = 0.5  # fraction of observed transits that must coincide
    transit_max_fap: float = 0.01  # binomial false-alarm probability P(X >= k | n, f)
    transit_residual_floor_hours: float = 0.25  # floor of the observed-residual window
    transit_flag_max_fap: float = 0.1  # marginal coincidence -> notes token, severity P2
    # Integer-harmonic matching on the host (audit G7, Thompson+2018)
    harmonic_max_n: int = 50
    harmonic_rel_tol_min: float = 0.001
    harmonic_max_fap: float = 0.05
    # Run-level systematics (audit A8)
    epoch_spike_bin_days: float = 0.25
    epoch_spike_factor: float = 2.0  # spike: count >= factor * median count per bin...
    epoch_spike_z: float = 6.0  # ...and >= median + z * max(1.4826 MAD, sqrt(median))...
    epoch_spike_min_count: int = 5  # ...and >= this many distinct other targets
    epoch_spike_min_targets: int = 100  # fewer contributing targets -> fraction is NULL
    epoch_spike_max_transits: int = 5  # only few-transit signals build the histogram
    epoch_spike_min_hits: int = 2  # fewer transits inside spikes -> fraction set to 0
    epoch_spike_max_frac: float = 0.5  # severity: >= this fraction = systematic, no alert
    shared_signal_radius_arcsec: float = 120.0
    duplicate_radius_arcsec: float = 2.0  # likely TIC duplicate/split (Paegert+2021)
    shared_signal_period_tol_min: float = 0.001
    shared_signal_period_tol_max: float = 0.01
    shared_signal_flux_ratio_max: float = 0.5  # comparable eclipsed flux beyond 1 px: both victims

    def max_age_hours(self, source: str) -> float | None:
        """Maximum mirror age for `source` (None = static catalog: no age limit)."""
        if source in self.static_sources:
            return None
        return self.mirror_max_age_hours_by_source.get(source, self.mirror_max_age_hours)

    def stale_sources(self, ages: dict) -> list[str]:
        """Sources missing (age None) or older than their limit. Keys may be enums or str."""
        out = []
        for key, age in ages.items():
            name = getattr(key, "value", key)
            limit = self.max_age_hours(name)
            if age is None or (limit is not None and age > limit):
                out.append(name)
        return sorted(out)

    def period_tolerance(self, period_days: float, period_err_days: float | None) -> float:
        """max(period_rel_tol, 3 sigma_rel of the candidate), capped at period_rel_tol_max."""
        rel = 0.0
        if period_err_days is not None and period_days > 0 and period_err_days == period_err_days:
            rel = 3.0 * abs(period_err_days) / period_days
        return min(max(self.period_rel_tol, rel), self.period_rel_tol_max)


class SeverityConfig(BaseModel):
    """Severity rules (alerts/severity.py, docs/PLAN.md §7)."""

    score_min_p1: float = 0.8  # deterministic vetting score needed for P0/P1
    p0_fpp_max: float = 0.1
    p0_nfpp_max: float = 1e-3  # Giacalone+2021 validation region
    nfpp_fail: float = 0.1  # likely nearby false positive: capped at P2
    p0_rp_max_rearth: float = 8.0
    p0_snr_min: float = 15.0
    p0_require_2min: bool = True
    two_min_authors: list[str] = Field(default_factory=lambda: ["SPOC"])
    epoch_spike_max_frac_default: float = 0.5  # used if crossmatch.epoch_spike_max_frac is absent
    p1_cut_fallback: float = 0.8  # model without operating points (schema 1)
    p2_cut_fallback: float = 0.5
    p2_recall_target: float = 0.90
    p1_recall_target: float = 0.70
    p1_fpr_max: float = 0.01
    new_prior: float = 0.05  # assumed planet fraction among NEW signals (p_abs only)


class Config(BaseModel):
    version: int = 1
    preprocess: PreprocessConfig = Field(default_factory=PreprocessConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    vetting: VettingConfig = Field(default_factory=VettingConfig)
    crossmatch: CrossmatchConfig = Field(default_factory=CrossmatchConfig)
    severity: SeverityConfig = Field(default_factory=SeverityConfig)

    def params_hash(self) -> str:
        """Short hash of the parameters, stored as provenance on every signal."""
        blob = json.dumps(self.model_dump(), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:12]


def load_config(path: Path | None = None) -> Config:
    path = path or Path(os.environ.get("PLANETHUNTER_CONFIG", DEFAULT_CONFIG))
    if not path.exists():
        return Config()
    with path.open(encoding="utf-8") as fh:
        return Config.model_validate(yaml.safe_load(fh) or {})


def data_dir() -> Path:
    """Data root (gitignored). Override with PLANETHUNTER_DATA."""
    d = Path(os.environ.get("PLANETHUNTER_DATA", REPO_ROOT / "data"))
    d.mkdir(parents=True, exist_ok=True)
    return d
