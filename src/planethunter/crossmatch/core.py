"""The "is it already known?" engine: deterministic classification of a signal vs known objects.

Two separate questions:
1. Which star? (exact ID or position; resolved by `crossmatch.batch.select_objects`)
2. Which signal? Evidence collected against every object on the host, then on neighbors:
   a. period with aliases {1, 2, 1/2, 3, 1/3, 3/2, 2/3}, reinforced by the T0 phase;
   b. integer harmonics n or 1/n (n <= 50; EBs also n/2), host only, phase mandatory and a
      chance probability below `harmonic_max_fap` (Thompson+2018; audit G7);
   c. period-less TOIs/CTOIs: the candidate ephemeris must predict the known epoch;
   d. transit by transit: >= 50 % of the observed transits coincide with known ephemerides
      AND the binomial false-alarm probability is below `transit_max_fap` (audit A9).

Only a matching star AND signal make the object known. A known host with no compatible
signal becomes NEW with host_known=True: that is the additional-planet niche.

Period policy:
- Tolerance = max(1 %, 3 sigma_rel of the candidate), capped at 3 %. Beyond 1 % the phase
  check is mandatory (audit B9: 2665 vs TOI-341.01).
- Alias 1 within 1 %: KNOWN even with an inconsistent phase (old ephemerides drift; two
  planets with the same period around one star do not exist).
- Alias != 1: requires a consistent phase when it can be checked; otherwise planets near
  2:1, 3:2, 3:1 resonance (usually 1-2 % off exact) would be swallowed as aliases.
- Eclipsing binaries and FP/FA/EB dispositions: any alias in tolerance is KNOWN_FP, at any
  phase (secondary and eccentric eclipses); no resonance exemption for binaries (audit A10).
- A catalog period without an error uses `default_period_rel_err` x P (never zero drift).
  When the propagated phase tolerance reaches 0.5 the phase is not informative and the
  match records phase_checked=False.

Precedence when several objects match on the host (all evidence is collected first):
confirmed planet > TFOPWG FP/FA > TOI > CTOI > published candidate > EB catalog.

No network, no disk. The caller supplies the mirror objects and the age of each mirror.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction

from planethunter.config import CrossmatchConfig

ALIASES: tuple[Fraction, ...] = (
    Fraction(1),
    Fraction(2),
    Fraction(1, 2),
    Fraction(3),
    Fraction(1, 3),
    Fraction(3, 2),
    Fraction(2, 3),
)

# Stable token in crossmatch.notes: the host has a TOI/CTOI/published candidate without a
# usable period (or epoch) that the candidate ephemeris could not be tested against.
# Severity caps such NEW signals at P2.
PERIODLESS_TOKEN = "periodless_known_on_host"
# Stable token: >= transit_min_fraction of the transits coincide with known ephemerides but
# the chance probability is only marginal (transit_max_fap <= fap < transit_flag_max_fap).
# Not enough to call it KNOWN (chance matches), too much to alert on. Severity: cap at P2.
PARTIAL_TRANSIT_TOKEN = "partial_known_transit_coincidence"


class MatchClass(StrEnum):
    KNOWN_PLANET = "KNOWN_PLANET"
    KNOWN_TOI = "KNOWN_TOI"
    KNOWN_CTOI = "KNOWN_CTOI"
    KNOWN_PUBLISHED = "KNOWN_PUBLISHED"  # refereed/cataloged candidate outside TOI/CTOI
    KNOWN_FP = "KNOWN_FP"
    NEARBY_KNOWN = "NEARBY_KNOWN"
    NEW = "NEW"
    UNVERIFIED = "UNVERIFIED"  # mirror missing or stale: alerting forbidden


class Source(StrEnum):
    ARCHIVE_PLANET = "archive_pscomppars"
    EXOPLANET_EU = "exoplanet_eu"
    TOI = "toi"
    CTOI = "ctoi"
    EB_CATALOG = "eb_catalog"  # Prsa+2022 TESS EBs (sectors 1-26)
    KOI = "koi_cumulative"  # Kepler KOI cumulative table (Archive TAP)
    K2 = "k2_pandc"  # K2 planets and candidates (Archive TAP)
    EB_KOSTOV2025 = "eb_kostov2025"  # TESS Ten Thousand EBs (Kostov+2025)
    PUB_DIAMANTE = "pub_diamante"  # Montalto+2020
    PUB_DTARPS = "pub_dtarps"  # Melton+2024 DTARPS-S
    PUB_LEO_VETTER = "pub_leo_vetter"  # Kunimoto+2025
    PUB_EXOMINERPP = "pub_exominerpp"  # Valizadegan+2025 ExoMiner++ PCs


EB_SOURCES = frozenset({Source.EB_CATALOG, Source.EB_KOSTOV2025})
# Sources whose objects were found by transit photometry (a missing period matters).
TRANSIT_SOURCES = frozenset(
    {
        Source.TOI,
        Source.CTOI,
        Source.KOI,
        Source.K2,
        Source.PUB_DIAMANTE,
        Source.PUB_DTARPS,
        Source.PUB_LEO_VETTER,
        Source.PUB_EXOMINERPP,
    }
)
FP_DISPOSITIONS = frozenset({"FP", "FA", "EB"})  # EB: TESS Disposition for an eclipsing binary
PLANET_DISPOSITIONS = frozenset({"CP", "KP"})


@dataclass(frozen=True)
class KnownObject:
    """Object from a mirror, already normalized. Time in BTJD, period in days."""

    source: Source
    name: str
    tic_id: int | None
    period_days: float | None
    t0_btjd: float | None = None
    period_err_days: float | None = None
    disposition: str | None = None  # CP, KP, PC, APC, FP, FA, EB
    separation_arcsec: float = 0.0


@dataclass(frozen=True)
class PeriodMatch:
    alias: Fraction  # P_candidate / P_known
    rel_err: float
    phase_checked: bool
    phase_consistent: bool | None
    phase_residual: float | None  # fraction of the common period grid
    kind: str = "period"  # period | harmonic | epoch
    chance: float | None = None  # chance probability (harmonic matches)


@dataclass
class CrossmatchResult:
    match_class: MatchClass
    host_known: bool
    matched: list[tuple[KnownObject, PeriodMatch | None]] = field(default_factory=list)
    match_type: str | None = None  # period | harmonic | epoch | transit_times
    host_eb: bool = False  # host is in an EB catalog: severity ceiling P2
    host_objects_checked: int = 0
    nearby_objects_checked: int = 0
    notes: list[str] = field(default_factory=list)
    stale_sources: list[str] = field(default_factory=list)

    @property
    def best(self) -> KnownObject | None:
        return self.matched[0][0] if self.matched else None

    @property
    def phase_checked(self) -> bool | None:
        """Was the decisive match confirmed in time? None when nothing matched."""
        if not self.matched:
            return None
        pm = self.matched[0][1]
        return pm.phase_checked if pm is not None else True


def _pos(x: float | None) -> bool:
    return x is not None and math.isfinite(x) and x > 0


def _finite(x: float | None) -> bool:
    return x is not None and math.isfinite(x)


def _sigma_p(o: KnownObject, cfg: CrossmatchConfig) -> float:
    assert o.period_days is not None
    return (
        o.period_err_days if _pos(o.period_err_days) else cfg.default_period_rel_err * o.period_days
    )


def is_binary_or_fp(o: KnownObject) -> bool:
    return o.source in EB_SOURCES or (o.disposition or "").upper() in FP_DISPOSITIONS


def _class_for(obj: KnownObject) -> MatchClass:
    disp = (obj.disposition or "").upper()
    if obj.source in EB_SOURCES or disp in FP_DISPOSITIONS:
        return MatchClass.KNOWN_FP
    if obj.source == Source.ARCHIVE_PLANET or disp in PLANET_DISPOSITIONS:
        return MatchClass.KNOWN_PLANET
    if obj.source == Source.TOI:
        return MatchClass.KNOWN_TOI
    if obj.source == Source.CTOI:
        return MatchClass.KNOWN_CTOI
    return MatchClass.KNOWN_PUBLISHED


def _priority(obj: KnownObject) -> int:
    """Which evidence sets the class when several objects match on the same host.

    Confirmed planet > TFOPWG FP/FA disposition > TOI > CTOI > published candidate > EB
    catalog. The TESS EB catalog (Prsa+2022) contains confirmed hot Jupiters: in sector 69,
    all 9 matches against it were WASP-18 b, WASP-100 b, HATS-16 b etc. That is why it loses.
    """
    cls = _class_for(obj)
    if cls == MatchClass.KNOWN_PLANET:
        return 0
    if cls == MatchClass.KNOWN_FP and obj.source not in EB_SOURCES:
        return 1
    return {
        MatchClass.KNOWN_TOI: 2,
        MatchClass.KNOWN_CTOI: 3,
        MatchClass.KNOWN_PUBLISHED: 4,
    }.get(cls, 5)


_KIND_RANK = {"period": 0, "harmonic": 1, "epoch": 2, "transit_times": 3}


def match_period(
    p_cand: float,
    t0_cand: float | None,
    p_known: float,
    t0_known: float | None,
    *,
    rel_tol: float,
    phase_tol: float,
    p_known_err: float | None = None,
    default_rel_err: float = 0.0,
    secondary: bool = False,
) -> PeriodMatch | None:
    """Match periods allowing for aliases {1, 2, 1/2, 3, 1/3, 3/2, 2/3}.

    For alias a/b, both transits fall on a common grid with step P_known / b. Phase is
    checked on that grid, with the tolerance widened by 3x the period uncertainty propagated
    to the candidate's epoch (sigma_P = p_known_err, or default_rel_err x P_known when the
    catalog gives none). `secondary` also accepts the phase-0.5 sequence (EB secondaries).
    A propagated tolerance >= 0.5 makes the phase uninformative: phase_checked=False.
    """
    if not (_pos(p_cand) and _pos(p_known)):
        return None
    ratio = p_cand / p_known
    best: tuple[Fraction, float] | None = None
    for k in ALIASES:
        err = abs(ratio / float(k) - 1.0)
        if err <= rel_tol and (best is None or err < best[1]):
            best = (k, err)
    if best is None:
        return None
    alias, rel_err = best
    if not (_finite(t0_cand) and _finite(t0_known)):
        return PeriodMatch(alias, rel_err, False, None, None)
    assert t0_cand is not None and t0_known is not None
    sig = p_known_err if _pos(p_known_err) else default_rel_err * p_known
    grid = p_known / alias.denominator
    n = round((t0_cand - t0_known) / grid)
    drift = abs(n) * sig / alias.denominator
    tol = phase_tol + 3.0 * drift / grid
    residual = _residual(t0_cand, t0_known, grid, p_known if secondary else None)
    if tol >= 0.5:
        return PeriodMatch(alias, rel_err, False, None, residual)
    return PeriodMatch(alias, rel_err, True, abs(residual) <= tol, residual)


def _residual(t_cand: float, t_ref: float, grid: float, p_secondary: float | None) -> float:
    """Signed phase residual on `grid`, optionally the smaller of primary/secondary."""
    refs = [t_ref] if p_secondary is None else [t_ref, t_ref + 0.5 * p_secondary]
    best = None
    for ref in refs:
        n = round((t_cand - ref) / grid)
        r = (t_cand - (ref + n * grid)) / grid
        if best is None or abs(r) < abs(best):
            best = r
    assert best is not None
    return best


def match_harmonic(
    p_cand: float,
    t0_cand: float | None,
    obj: KnownObject,
    cfg: CrossmatchConfig,
    *,
    p_cand_err: float | None,
    duration_days: float | None,
) -> PeriodMatch | None:
    """Integer harmonic P_cand = n x P_known or P_known / n (n <= harmonic_max_n).

    EBs/FPs also allow n/2 (equal primary and secondary eclipses: e.g. 7/2). Requires both
    T0 and a consistent phase: |residual| <= max(0.5 D, floor) + 3 sigma_prop on the common
    grid P_known / b. Accepted only if the chance probability, P(period coincidence) x
    P(phase coincidence) = min(1, 2 tol max(r, 1/r) / step) x min(1, 2 w / grid), is below
    harmonic_max_fap. Ratios in the alias set are left to `match_period`.
    """
    if not (_pos(p_cand) and _pos(obj.period_days)) or not (
        _finite(t0_cand) and _finite(obj.t0_btjd)
    ):
        return None
    assert obj.period_days is not None and t0_cand is not None and obj.t0_btjd is not None
    p_k = obj.period_days
    step = Fraction(1, 2) if is_binary_or_fp(obj) else Fraction(1)
    r = p_cand / p_k
    if r >= 1:
        q = Fraction(round(r / float(step))) * step
    else:
        m = round((1 / r) / float(step))
        if m == 0:
            return None
        q = 1 / (Fraction(m) * step)
    if q <= 0 or q in ALIASES or max(q, 1 / q) > cfg.harmonic_max_n:
        return None
    rel_err = abs(r / float(q) - 1.0)
    sig_rel_c = 3.0 * p_cand_err / p_cand if _pos(p_cand_err) else 0.0
    tol = min(max(cfg.harmonic_rel_tol_min, sig_rel_c), cfg.period_rel_tol_max)
    if rel_err > tol:
        return None
    grid = p_k / q.denominator
    # EB/FP: the secondary (phase 0.5) is also a valid reference; for q = n/2 it is already
    # on the P_k/2 grid.
    secondary = is_binary_or_fp(obj) and q.denominator == 1
    n = round((t0_cand - obj.t0_btjd) / grid)
    sig_prop = abs(n) * _sigma_p(obj, cfg) / q.denominator
    half = max(0.5 * (duration_days or 0.0), cfg.transit_window_floor_hours / 24.0)
    w = half + 3.0 * sig_prop
    residual_days = _residual(t0_cand, obj.t0_btjd, grid, p_k if secondary else None) * grid
    if abs(residual_days) > w:
        return None
    p_period = min(1.0, 2.0 * tol * max(r, 1.0 / r) / float(step))
    p_phase = min(1.0, (2 if secondary else 1) * 2.0 * w / grid)
    chance = p_period * p_phase
    if chance >= cfg.harmonic_max_fap:
        return None
    return PeriodMatch(q, rel_err, True, True, residual_days / grid, "harmonic", chance)


def match_epoch(
    p_cand: float,
    t0_cand: float | None,
    obj: KnownObject,
    cfg: CrossmatchConfig,
    *,
    p_cand_err: float | None,
    duration_days: float | None,
) -> PeriodMatch | None | bool:
    """Period-less known object with an epoch: does the candidate ephemeris predict it?

    Returns a PeriodMatch on a hit, None on an informative miss, False when untestable
    (no epoch, or the candidate ephemeris propagated to the known epoch has 3 sigma >
    min(transit_max_unc_days, transit_max_unc_frac x P)).
    """
    if not (_pos(p_cand) and _finite(t0_cand) and _finite(obj.t0_btjd)):
        return False
    assert t0_cand is not None and obj.t0_btjd is not None
    n = round((obj.t0_btjd - t0_cand) / p_cand)
    sig_c = p_cand_err if _pos(p_cand_err) else cfg.default_period_rel_err * p_cand
    unc = 3.0 * abs(n) * sig_c
    if unc > min(cfg.transit_max_unc_days, cfg.transit_max_unc_frac * p_cand):
        return False
    half = max(0.5 * (duration_days or 0.0), cfg.transit_window_floor_hours / 24.0)
    resid = obj.t0_btjd - (t0_cand + n * p_cand)
    if abs(resid) <= half + unc:
        return PeriodMatch(Fraction(1), 0.0, True, True, resid / p_cand, "epoch")
    return None


@dataclass(frozen=True)
class TransitEvidence:
    """Per observed transit, every known object whose ephemeris predicts an event there."""

    per_transit: list[list[KnownObject]]
    coverage: float  # union fractional coverage of the full windows (chance per transit)
    k: int  # transits explained
    n: int  # transits observed
    fap: float  # binomial P(X >= k | n, f_obs)
    max_residual_days: float | None = None  # largest |t_obs - t_pred| among explained transits
    coverage_obs: float | None = None  # f_obs: coverage of windows shrunk to that residual


def binom_sf(k: int, n: int, f: float) -> float:
    """P(X >= k) for X ~ Binomial(n, f)."""
    if k <= 0:
        return 1.0
    f = min(max(f, 0.0), 1.0)
    return sum(math.comb(n, j) * f**j * (1.0 - f) ** (n - j) for j in range(k, n + 1))


def _clusters(objs: list[KnownObject], rel: float = 1e-3) -> list[list[KnownObject]]:
    """Group objects with the same period (the same planet listed by several catalogs)."""
    out: list[list[KnownObject]] = []
    for o in sorted(objs, key=lambda x: x.period_days or 0.0):
        assert o.period_days is not None
        ref = out[-1][-1].period_days if out else None
        if ref is not None and abs(o.period_days / ref - 1.0) <= rel:
            out[-1].append(o)
        else:
            out.append([o])
    return out


def explain_transits(
    transit_times: list[float],
    duration_days: float,
    objects: list[KnownObject],
    cfg: CrossmatchConfig,
) -> TransitEvidence:
    """Transit-by-transit matcher (audit A9).

    With a single sector, TLS can combine transits of DIFFERENT planets in a system into a
    spurious period (sector 69: HD 23472, TOI-703, GJ 143 gave "new planets" at 10.29, 11.40
    and 8.80 d). A transit is explained by an object when |t - t_pred| <= max(0.5 D, floor)
    + 3 sigma_prop. Objects whose 3 sigma_prop > min(transit_max_unc_days,
    transit_max_unc_frac x P) are skipped. Phase 0.5 (secondary eclipse) is tested only for
    non-planet objects (EB, FP, PC, APC, CTOI, published candidates), never when the same
    period is a confirmed planet in any catalog.

    Chance probability: objects with the same period (one planet in several catalogs) form
    one cluster, so their windows are counted once. The test statistic is the largest
    residual r among the explained transits; under the null a transit falls that close to
    some known event with probability f_obs = sum over clusters of
    n_phases x 2 max(r, transit_residual_floor) / P (capped at the full windows), and
    fap = P(X >= k | n, f_obs). The old loose version (window up to D + 1 d, phase 0.5 for
    everything, closest object only, no chance test) fired by chance 36 % of the time.
    """
    half = max(0.5 * duration_days, cfg.transit_window_floor_hours / 24.0)
    t_mean = sum(transit_times) / len(transit_times) if transit_times else 0.0
    cand: list[tuple[KnownObject, float, float]] = []  # (object, sigma_P, 3 sigma_prop)
    for o in objects:
        if not (_pos(o.period_days) and _finite(o.t0_btjd)):
            continue
        assert o.period_days is not None and o.t0_btjd is not None
        sig = _sigma_p(o, cfg)
        unc = 3.0 * abs(round((t_mean - o.t0_btjd) / o.period_days)) * sig
        if unc > min(cfg.transit_max_unc_days, cfg.transit_max_unc_frac * o.period_days):
            continue
        cand.append((o, sig, unc))
    info = {id(o): (sig, unc) for o, sig, unc in cand}
    usable: list[tuple[KnownObject, float, tuple[float, ...]]] = []
    windows: list[tuple[float, int, float]] = []  # per cluster: (P, n_phases, max window)
    for cl in _clusters([o for o, _, _ in cand]):
        planet = any(_class_for(o) == MatchClass.KNOWN_PLANET for o in cl)
        offsets = (0.0,) if planet else (0.0, 0.5)
        for o in cl:
            usable.append((o, info[id(o)][0], offsets))
        w_max = max(half + info[id(o)][1] for o in cl)
        windows.append((float(cl[0].period_days or 0.0), len(offsets), w_max))
    coverage = min(1.0, sum(min(1.0, m * 2.0 * w / p) for p, m, w in windows))
    per: list[list[KnownObject]] = []
    r_max: float | None = None
    for tt in transit_times:
        hits: list[KnownObject] = []
        best_r: float | None = None
        for o, sig, offsets in usable:
            assert o.period_days is not None and o.t0_btjd is not None
            for off in offsets:
                ref = o.t0_btjd + off * o.period_days
                n = round((tt - ref) / o.period_days)
                r = abs(tt - (ref + n * o.period_days))
                if r <= half + 3.0 * abs(n) * sig:
                    hits.append(o)
                    best_r = r if best_r is None else min(best_r, r)
                    break
        per.append(hits)
        if best_r is not None:
            r_max = best_r if r_max is None else max(r_max, best_r)
    k = sum(1 for h in per if h)
    n = len(per)
    if not k or r_max is None:
        return TransitEvidence(per, coverage, k, n, 1.0)
    r_eff = max(r_max, cfg.transit_residual_floor_hours / 24.0)
    f_obs = min(1.0, sum(min(1.0, m * 2.0 * min(w, r_eff) / p) for p, m, w in windows))
    return TransitEvidence(per, coverage, k, n, binom_sf(k, n, f_obs), r_max, f_obs)


def _host_eb(host_objects: list[KnownObject], cfg: CrossmatchConfig) -> bool:
    """Host is in an EB catalog, ignoring EB rows that are a planet/PC on the same host.

    The TESS EB catalogs contain hot Jupiters (WASP-173 A b, WASP-18 b...). An EB row whose
    period matches a non-FP row of the host at alias 1 is that planet, not a binary.
    """
    others = [
        o
        for o in host_objects
        if o.source not in EB_SOURCES and not is_binary_or_fp(o) and _pos(o.period_days)
    ]
    for eb in host_objects:
        if eb.source not in EB_SOURCES:
            continue
        if _pos(eb.period_days) and any(
            abs(eb.period_days / o.period_days - 1.0) <= cfg.period_rel_tol  # type: ignore[operator]
            for o in others
        ):
            continue
        return True
    return False


def _period_matches(
    period_days: float,
    t0_btjd: float | None,
    objects: list[KnownObject],
    cfg: CrossmatchConfig,
    tol: float,
    resonant: list[str],
) -> list[tuple[KnownObject, PeriodMatch]]:
    out = []
    for o in objects:
        if not _pos(o.period_days):
            continue
        assert o.period_days is not None
        fp = is_binary_or_fp(o)
        m = match_period(
            period_days,
            t0_btjd,
            o.period_days,
            o.t0_btjd,
            rel_tol=tol,
            phase_tol=cfg.phase_tol,
            p_known_err=o.period_err_days,
            default_rel_err=cfg.default_period_rel_err,
            secondary=fp,
        )
        if m is None:
            continue
        if m.rel_err > cfg.period_rel_tol:
            # Beyond the 1 % floor (tolerance widened by the candidate's sigma_P): only a
            # confirmed phase makes it the same object.
            if m.phase_checked and m.phase_consistent:
                out.append((o, m))
            continue
        if fp or m.alias == 1:
            out.append((o, m))
            continue
        if m.phase_checked and not m.phase_consistent:
            resonant.append(o.name)
            continue
        out.append((o, m))
    return out


def _sort_key(om: tuple[KnownObject, PeriodMatch | None]) -> tuple:
    o, m = om
    kind = m.kind if m is not None else "transit_times"
    return (
        _priority(o),
        _KIND_RANK[kind],
        m is not None and m.alias != 1,
        m.rel_err if m is not None else 0.0,
    )


def classify(
    period_days: float,
    t0_btjd: float | None,
    host_objects: list[KnownObject],
    nearby_objects: list[KnownObject],
    mirror_age_hours: dict[Source, float | None],
    cfg: CrossmatchConfig,
    *,
    transit_times: list[float] | None = None,
    duration_days: float | None = None,
    period_err_days: float | None = None,
) -> CrossmatchResult:
    """Classify a signal. `host_objects` = objects on the same target (by ID or 21" cone).

    `nearby_objects` = objects within cfg.nearby_radius_arcsec. `mirror_age_hours` must
    contain ALL sources in Source; missing or stale (per-source policy) -> UNVERIFIED.
    `period_err_days` is the candidate's sigma_P (widens the period tolerance up to 3 %).
    """
    ages = {s: mirror_age_hours.get(s) for s in Source}
    stale = cfg.stale_sources(ages)
    tol = cfg.period_tolerance(period_days, period_err_days)
    resonant: list[str] = []
    result = CrossmatchResult(
        match_class=MatchClass.NEW,
        host_eb=_host_eb(host_objects, cfg),
        host_known=bool(host_objects),
        host_objects_checked=len(host_objects),
        nearby_objects_checked=len(nearby_objects),
        stale_sources=stale,
    )

    # ---- host: collect every piece of evidence, then apply precedence
    evidence: list[tuple[KnownObject, PeriodMatch | None]] = list(
        _period_matches(period_days, t0_btjd, host_objects, cfg, tol, resonant)
    )
    matched_ids = {id(o) for o, _ in evidence}
    untestable: list[str] = []
    for o in host_objects:
        if id(o) in matched_ids:
            continue
        if _pos(o.period_days):
            h = match_harmonic(
                period_days,
                t0_btjd,
                o,
                cfg,
                p_cand_err=period_err_days,
                duration_days=duration_days,
            )
            if h is not None:
                evidence.append((o, h))
        elif o.source in TRANSIT_SOURCES and not is_binary_or_fp(o):
            e = match_epoch(
                period_days,
                t0_btjd,
                o,
                cfg,
                p_cand_err=period_err_days,
                duration_days=duration_days,
            )
            if isinstance(e, PeriodMatch):
                evidence.append((o, e))
            else:
                untestable.append(o.name)
    te = ten = None
    if transit_times and duration_days:
        te = explain_transits(transit_times, duration_days, host_objects, cfg)
        if _transits_accepted(te, cfg):
            seen = {id(o) for o, _ in evidence}
            for hits in te.per_transit:
                for o in hits:
                    if id(o) not in seen:
                        evidence.append((o, None))
                        seen.add(id(o))

    if evidence:
        evidence.sort(key=_sort_key)
        best_o, best_m = evidence[0]
        result.match_class = _class_for(best_o)
        result.matched = evidence
        result.match_type = best_m.kind if best_m is not None else "transit_times"
        if best_m is None and te is not None:
            result.notes.append(_transit_note(te))
        elif best_m is not None and best_m.kind == "period" and not best_m.phase_consistent:
            result.notes.append(
                "period matches but phase not confirmed; ephemeris may have drifted"
            )
        elif best_m is not None and best_m.kind == "harmonic":
            result.notes.append(
                f"integer harmonic {best_m.alias} of {best_o.name} "
                f"(chance probability {best_m.chance:.2g})"
            )
    else:
        # ---- neighbors: the signal may come from a nearby known object (contamination)
        near: list[tuple[KnownObject, PeriodMatch | None]] = list(
            _period_matches(period_days, t0_btjd, nearby_objects, cfg, tol, [])
        )
        if transit_times and duration_days:
            ten = explain_transits(transit_times, duration_days, nearby_objects, cfg)
            if _transits_accepted(ten, cfg):
                seen = {id(o) for o, _ in near}
                for hits in ten.per_transit:
                    for o in hits:
                        if id(o) not in seen:
                            near.append((o, None))
                            seen.add(id(o))
                if not any(m is not None for _, m in near):
                    result.notes.append(_transit_note(ten))
        if near:
            near.sort(key=lambda om: (om[0].separation_arcsec, _sort_key(om)))
            result.match_class = MatchClass.NEARBY_KNOWN
            result.matched = near
            result.match_type = near[0][1].kind if near[0][1] is not None else "transit_times"
            result.notes.append("signal likely comes from a nearby known object (contamination)")
        elif host_objects:
            result.notes.append(
                "host already has known objects; new period = possible additional planet"
            )
    if result.match_class == MatchClass.NEW:
        if resonant:
            result.notes.append(
                f"period near resonance with {sorted(set(resonant))}, distinct phase"
            )
        marginal = [t for t in (te, ten) if t is not None and _transits_marginal(t, cfg)]
        if marginal:
            result.notes.append(f"{PARTIAL_TRANSIT_TOKEN}: " + _transit_note(marginal[0]))
        if untestable:
            result.notes.append(
                f"{PERIODLESS_TOKEN}: {sorted(set(untestable))} have no period and their "
                "epoch is missing, untestable or not predicted by the candidate ephemeris"
            )
    if stale and result.match_class == MatchClass.NEW:
        result.match_class = MatchClass.UNVERIFIED
        result.notes.append(f"mirrors missing or stale for their freshness policy: {stale}")
    return result


def _transits_accepted(te: TransitEvidence, cfg: CrossmatchConfig) -> bool:
    return te.k > 0 and te.k / te.n >= cfg.transit_min_fraction and te.fap < cfg.transit_max_fap


def _transits_marginal(te: TransitEvidence, cfg: CrossmatchConfig) -> bool:
    return (
        te.k > 0
        and te.k / te.n >= cfg.transit_min_fraction
        and cfg.transit_max_fap <= te.fap < cfg.transit_flag_max_fap
    )


def _transit_note(te: TransitEvidence) -> str:
    names = sorted({o.name for hits in te.per_transit for o in hits})
    return (
        f"{te.k} of {te.n} transits coincide with {names} (chance {te.fap:.1e}, max residual "
        f"{(te.max_residual_days or 0.0) * 24:.2f} h): period likely spurious (transits of "
        "known objects combined)"
    )
