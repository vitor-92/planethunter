"""Data types shared between stages. Units in the name or in the docstring."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

LOGG_SUN_CGS = 4.438  # log10(g_sun) in cm/s^2


@dataclass(frozen=True)
class StarParams:
    """Stellar parameters (TIC, via FITS header). Radius in R_sun, mass in M_sun."""

    tic_id: int
    ra_deg: float | None = None
    dec_deg: float | None = None
    pmra_mas_yr: float | None = None
    pmdec_mas_yr: float | None = None
    tmag: float | None = None
    teff_k: float | None = None
    logg_cgs: float | None = None
    radius_rsun: float | None = None
    mass_msun: float | None = None
    crowdsap: float | None = None  # fraction of the aperture flux coming from the target (SPOC)

    def mass_or_estimate(self) -> float | None:
        """TIC mass; if missing, estimate from logg and radius: M = g R^2 / G (solar units)."""
        if _ok(self.mass_msun):
            return self.mass_msun
        if _ok(self.logg_cgs) and _ok(self.radius_rsun):
            return 10 ** (self.logg_cgs - LOGG_SUN_CGS) * self.radius_rsun**2
        return None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Signal:
    """Detected periodic signal. Time in BTJD, period in days, depth in ppm."""

    tic_id: int
    sectors: str  # e.g. "1,27,67"
    author: str
    iteration: int
    period_days: float
    period_err_days: float
    t0_btjd: float
    duration_hours: float
    depth_ppm: float
    sde: float
    snr: float
    n_transits: int  # transits with data
    odd_even_mismatch_sigma: float
    rp_rs: float
    fap: float
    alias_factor: int = 1  # period = alias_factor * TLS period (refine_alias)
    detrend_window_days: float = float("nan")
    transit_times_json: str = "[]"  # BTJD of the transits with data
    edge_transit_fraction: float = 0.0  # fraction of transits with data at segment edges
    run_id: str = ""
    pipeline_version: str = ""
    params_hash: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("extra")
        return d


def _ok(x: float | None) -> bool:
    return x is not None and isinstance(x, int | float) and math.isfinite(x) and x > 0
