"""Severity of a candidate. Pure function; rules in docs/PLAN.md §7, thresholds in the
`severity:` section of config/thresholds.yaml.

Order of the rules:
1. Not NEW, or no score -> NONE.
2. Systematics and blends (crossmatch): >= crossmatch.epoch_spike_max_frac of the transits on
   run-level epoch spikes -> NONE; same P/T0 on another target where this one is the
   "duplicate" or the "victim" -> NONE.
3. A deterministic veto (score 0) -> NONE.
4. Failed basic vetting (no veto): NONE, unless the ML ranks it at p_rank >= p2_cut, in which
   case it is rescued at most to P2.
5. Ceiling P2: host is a cataloged EB; star without radius; this target is the "source" of a
   signal shared with neighbors; a period-less known object on the host
   ("periodless_known_on_host" in crossmatch.notes); NFPP > nfpp_fail (likely nearby FP).
6. P1 needs BOTH the deterministic score >= score_min_p1 AND (if a model exists)
   p_rank >= p1_cut. The ML can only lower priority, never raise it (audit A2: signals 3747 and
   3123 were promoted P2 -> P0/P1 by the ML alone).
7. P0 additionally needs complete deep vetting (TPF difference image and Gaia neighbors both
   passed, FPP computed and passed; audit A3), FPP < p0_fpp_max, and the Giacalone+2021
   validation region: NFPP < 1e-3, Rp < 8 R_earth, SNR >= 15, 2-min cadence, and no
   "outside validation region" flag from the FPP test. Anything not verifiable (None) caps at P1.
"""

from __future__ import annotations

from planethunter.config import SeverityConfig
from planethunter.crossmatch.core import MatchClass

BLOCKING_ROLES = frozenset({"duplicate", "victim"})
CAPPING_ROLES = frozenset({"source"})
PERIODLESS_TOKEN = "periodless_known_on_host"
PARTIAL_TRANSIT_TOKEN = "partial_known_transit_coincidence"


def _finite(x: float | None) -> bool:
    return x is not None and x == x  # NaN-safe


def severity(
    match_class: str,
    verdict: str | None,
    score: float | None,
    *,
    deep_done: bool = False,
    fpp: float | None = None,
    nfpp: float | None = None,
    host_eb: bool = False,
    star_known: bool = True,
    p_planet: float | None = None,
    p1_cut: float | None = None,
    p2_cut: float | None = None,
    rp_rearth: float | None = None,
    snr: float | None = None,
    two_min_cadence: bool | None = None,
    outside_validation_region: bool = False,
    epoch_spike_frac: float | None = None,
    epoch_spike_max_frac: float | None = None,
    shared_signal_role: str | None = None,
    periodless_known_on_host: bool = False,
    partial_known_transit: bool = False,
    cfg: SeverityConfig | None = None,
) -> str:
    """P0 | P1 | P2 | NONE.

    `score` is the deterministic vetting score; `p_planet` is the ML ranking probability
    (p_rank, already penalized by deep-vetting failures); `p1_cut`/`p2_cut` are the model's
    operating points (fallbacks from cfg when None).
    """
    cfg = cfg or SeverityConfig()
    if match_class != MatchClass.NEW.value or not _finite(score):
        return "NONE"
    spike_max = (
        cfg.epoch_spike_max_frac_default
        if not _finite(epoch_spike_max_frac)
        else float(epoch_spike_max_frac)
    )
    if _finite(epoch_spike_frac) and float(epoch_spike_frac) >= spike_max:
        return "NONE"  # transits on common-epoch systematics (audit A8)
    role = (shared_signal_role or "").strip().lower() or None
    if role in BLOCKING_ROLES:
        return "NONE"  # the same signal belongs to another target (TIC duplicate or blend)
    if score <= 0.0:
        return "NONE"  # deterministic veto
    p = float(p_planet) if _finite(p_planet) else None
    c1 = cfg.p1_cut_fallback if not _finite(p1_cut) else float(p1_cut)
    c2 = cfg.p2_cut_fallback if not _finite(p2_cut) else float(p2_cut)
    if verdict != "PASS_BASIC":
        return "P2" if p is not None and p >= c2 else "NONE"  # ML rescue, capped at P2
    if (
        host_eb  # a new signal on a cataloged EB is nearly always an eclipse (sig 1594)
        or not star_known  # no TIC radius: giant/atypical star (sig 1600)
        or role in CAPPING_ROLES
        or periodless_known_on_host
        or partial_known_transit  # transits partly on a known ephemeris (1e-2 <= chance < 0.1)
        or (_finite(nfpp) and float(nfpp) > cfg.nfpp_fail)
    ):
        return "P2"
    if score < cfg.score_min_p1:
        return "P2"
    if p is not None and p < c1:
        return "P2"  # the ML only lowers priority
    validation_region = (
        _finite(nfpp)
        and float(nfpp) < cfg.p0_nfpp_max
        and _finite(rp_rearth)
        and float(rp_rearth) < cfg.p0_rp_max_rearth
        and _finite(snr)
        and float(snr) >= cfg.p0_snr_min
        and (bool(two_min_cadence) or not cfg.p0_require_2min)
        and not outside_validation_region
    )
    if deep_done and _finite(fpp) and float(fpp) < cfg.p0_fpp_max and validation_region:
        return "P0"
    return "P1"
