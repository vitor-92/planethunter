from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

from planethunter.config import CrossmatchConfig
from planethunter.crossmatch import KnownObject, MatchClass, Source, classify, match_period
from planethunter.crossmatch.core import (
    PARTIAL_TRANSIT_TOKEN,
    PERIODLESS_TOKEN,
    binom_sf,
    explain_transits,
)

CFG = CrossmatchConfig()
FRESH = {s: 1.0 for s in Source}


def _m(pc, tc, pk, tk, **kw):
    return match_period(pc, tc, pk, tk, rel_tol=0.01, phase_tol=0.05, **kw)


@pytest.mark.parametrize(
    ("p_cand", "p_known", "alias"),
    [
        (2.0, 4.0, Fraction(1, 2)),
        (4.0, 2.0, Fraction(2)),
        (1.0, 3.0, Fraction(1, 3)),
        (3.0, 2.0, Fraction(3, 2)),
        (2.0, 3.0, Fraction(2, 3)),
        (5.0, 5.03, Fraction(1)),
    ],
)
def test_aliases_match(p_cand, p_known, alias):
    m = _m(p_cand, None, p_known, None)
    assert m is not None and m.alias == alias and not m.phase_checked


def test_non_alias_does_not_match():
    assert _m(2.0, None, 2.05, None) is None
    assert _m(2.0, None, 5.0, None) is None


def test_phase_consistency_on_alias_grid():
    # candidate at P/2 with T0 half a period later: the known transits are a subset.
    m = _m(2.0, 1000.0 + 2.0, 4.0, 1000.0)
    assert m.phase_consistent
    m = _m(2.0, 1000.0 + 1.0, 4.0, 1000.0)  # shifted by half a candidate period
    assert m.phase_checked and not m.phase_consistent


def test_phase_tolerance_grows_with_period_uncertainty():
    # 500 epochs later, a period error of 1e-4 d accumulates 0.05 d of drift.
    pk, err = 3.0, 1e-4
    t_cand = 1000.0 + 500 * pk + 0.25  # 0.083 in phase: would fail without propagating uncertainty
    assert not _m(pk, t_cand, pk, 1000.0).phase_consistent
    assert _m(pk, t_cand, pk, 1000.0, p_known_err=err).phase_consistent


def test_missing_period_error_uses_conservative_default():
    """Audit A10: a catalog without sigma_P must not mean zero drift."""
    pk = 3.0
    t_cand = 1000.0 + 500 * pk + 0.25
    assert not _m(pk, t_cand, pk, 1000.0).phase_consistent  # bare function: back-compatible
    assert _m(pk, t_cand, pk, 1000.0, default_rel_err=1e-4).phase_consistent


def test_uninformative_phase_is_not_checked():
    """Propagated tolerance >= 0.5: the phase says nothing -> phase_checked=False."""
    m = _m(3.0, 1000.0 + 2000 * 3.0 + 1.0, 3.0, 1000.0, p_known_err=1e-3)
    assert m is not None and not m.phase_checked and m.phase_consistent is None


def _obj(source, period, t0=None, disp=None, sep=0.0, name="X", err=None):
    return KnownObject(
        source=source,
        name=name,
        tic_id=1,
        period_days=period,
        t0_btjd=t0,
        period_err_days=err,
        disposition=disp,
        separation_arcsec=sep,
    )


def test_known_planet_on_host():
    r = classify(3.7, 1326.3, [_obj(Source.ARCHIVE_PLANET, 3.7, 1326.3)], [], FRESH, CFG)
    assert r.match_class == MatchClass.KNOWN_PLANET and r.host_known and r.phase_checked


def test_toi_and_ctoi_classes():
    assert (
        classify(3.7, None, [_obj(Source.TOI, 3.7, disp="PC")], [], FRESH, CFG).match_class
        == MatchClass.KNOWN_TOI
    )
    assert (
        classify(3.7, None, [_obj(Source.CTOI, 3.7, disp="PC")], [], FRESH, CFG).match_class
        == MatchClass.KNOWN_CTOI
    )
    assert (
        classify(3.7, None, [_obj(Source.TOI, 3.7, disp="KP")], [], FRESH, CFG).match_class
        == MatchClass.KNOWN_PLANET
    )


@pytest.mark.parametrize(
    ("source", "disp", "cls"),
    [
        (Source.EXOPLANET_EU, "PC", MatchClass.KNOWN_PUBLISHED),
        (Source.EXOPLANET_EU, "CP", MatchClass.KNOWN_PLANET),
        (Source.KOI, "PC", MatchClass.KNOWN_PUBLISHED),
        (Source.KOI, "CP", MatchClass.KNOWN_PLANET),
        (Source.K2, "FP", MatchClass.KNOWN_FP),
        (Source.PUB_DTARPS, "PC", MatchClass.KNOWN_PUBLISHED),
        (Source.PUB_EXOMINERPP, "PC", MatchClass.KNOWN_PUBLISHED),
        (Source.EB_KOSTOV2025, "EB", MatchClass.KNOWN_FP),
    ],
)
def test_new_sources_map_to_classes(source, disp, cls):
    assert classify(3.7, None, [_obj(source, 3.7, disp=disp)], [], FRESH, CFG).match_class == cls


def test_false_positive_wins_over_other_matches():
    host = [_obj(Source.CTOI, 3.7, disp="PC"), _obj(Source.TOI, 7.4, disp="FP")]
    assert classify(3.7, None, host, [], FRESH, CFG).match_class == MatchClass.KNOWN_FP


def test_additional_planet_on_known_host_is_new():
    """Invariant: a known host with a new period is NOT discarded."""
    r = classify(5.3, 1330.0, [_obj(Source.ARCHIVE_PLANET, 3.7, 1326.3)], [], FRESH, CFG)
    assert r.match_class == MatchClass.NEW and r.host_known
    assert any("additional" in n for n in r.notes)
    assert r.phase_checked is None


def test_near_resonant_additional_planet_is_not_swallowed_by_alias():
    """11.2 d is 0.9 % from 3 x 3.7 d. Distinct phase = another planet (near 3:1)."""
    r = classify(11.2, 1331.0, [_obj(Source.ARCHIVE_PLANET, 3.7, 1326.3)], [], FRESH, CFG)
    assert r.match_class == MatchClass.NEW and r.host_known
    assert any("resonance" in n for n in r.notes)


def test_true_alias_with_consistent_phase_is_known():
    """Same planet detected at twice the period (alternate transits)."""
    r = classify(7.4, 1326.3 + 3.7, [_obj(Source.TOI, 3.7, 1326.3, disp="PC")], [], FRESH, CFG)
    assert r.match_class == MatchClass.KNOWN_TOI


def test_period_match_with_bad_phase_on_host_is_still_known():
    """Conservative: a drifted ephemeris must not trigger an alert for a known planet."""
    r = classify(3.7, 1326.3 + 1.85, [_obj(Source.TOI, 3.7, 1326.3, disp="PC")], [], FRESH, CFG)
    assert r.match_class == MatchClass.KNOWN_TOI
    assert any("phase" in n for n in r.notes)


# ---------------------------------------------------------------- B9: period tolerance


def test_period_tolerance_widens_with_candidate_error_but_needs_phase():
    """Audit B9 (2665 vs TOI-341.01): 2.4 % off with sigma_P ~ 1 %; beyond 1 % phase decides."""
    toi = _obj(Source.TOI, 4.0, 1000.0, disp="PC", err=1e-5)
    p = 4.0 * 1.024
    t_in_phase = 1000.0 + 100 * 4.0
    r = classify(p, t_in_phase, [toi], [], FRESH, CFG, period_err_days=0.01 * p)
    assert r.match_class == MatchClass.KNOWN_TOI and r.phase_checked
    r = classify(p, t_in_phase + 1.5, [toi], [], FRESH, CFG, period_err_days=0.01 * p)
    assert r.match_class == MatchClass.NEW  # phase disagrees beyond the 1 % floor
    r = classify(p, None, [toi], [], FRESH, CFG, period_err_days=0.01 * p)
    assert r.match_class == MatchClass.NEW  # no phase available: the 1 % floor applies
    r = classify(p, t_in_phase, [toi], [], FRESH, CFG, period_err_days=1e-4 * p)
    assert r.match_class == MatchClass.NEW  # precise candidate: tolerance stays at 1 %


def test_period_tolerance_is_capped():
    assert CFG.period_tolerance(10.0, 1.0) == pytest.approx(0.03)
    assert CFG.period_tolerance(10.0, None) == pytest.approx(0.01)
    assert CFG.period_tolerance(10.0, 0.05) == pytest.approx(0.015)


# ---------------------------------------------------------------- A10: binaries


def test_eb_alias_with_any_phase_is_known_fp():
    """Audit A10 (2655, 4359): no resonance exemption for binaries."""
    eb = _obj(Source.EB_CATALOG, 2.0, 1000.0, disp="EB", err=1e-6)
    r = classify(4.0, 1000.0 + 0.7, [eb], [], FRESH, CFG)  # alias 2, phase off
    assert r.match_class == MatchClass.KNOWN_FP
    fp = _obj(Source.TOI, 3.0, 1000.0, disp="FP", err=1e-6)
    r = classify(4.5, 1000.0 + 1.1, [fp], [], FRESH, CFG)  # alias 3/2, phase off
    assert r.match_class == MatchClass.KNOWN_FP


def test_eb_secondary_phase_beyond_floor():
    """Beyond 1 % an EB match needs the phase, but the secondary (phase 0.5) counts."""
    eb = _obj(Source.EB_CATALOG, 4.0, 1000.0, disp="EB", err=1e-6)
    p = 4.0 * 1.02
    r = classify(p, 1000.0 + 50 * 4.0 + 2.0, [eb], [], FRESH, CFG, period_err_days=0.01 * p)
    assert r.match_class == MatchClass.KNOWN_FP
    planet = _obj(Source.ARCHIVE_PLANET, 4.0, 1000.0, err=1e-6)
    r = classify(p, 1000.0 + 50 * 4.0 + 2.0, [planet], [], FRESH, CFG, period_err_days=0.01 * p)
    assert r.match_class == MatchClass.NEW  # planets have no secondary eclipse at that depth


def test_stale_or_missing_mirror_blocks_new():
    ages = {**FRESH, Source.CTOI: 72.0}
    assert classify(9.9, None, [], [], ages, CFG).match_class == MatchClass.UNVERIFIED
    ages = {s: 1.0 for s in Source if s != Source.EB_CATALOG}
    assert classify(9.9, None, [], [], ages, CFG).match_class == MatchClass.UNVERIFIED
    assert classify(9.9, None, [], [], FRESH, CFG).match_class == MatchClass.NEW


def test_per_source_freshness_policy():
    """exoplanet.eu weekly, static VizieR catalogs never expire, ExoFOP stays at 48 h."""
    ages = {**FRESH, Source.EXOPLANET_EU: 100.0, Source.EB_KOSTOV2025: 10_000.0}
    assert classify(9.9, None, [], [], ages, CFG).match_class == MatchClass.NEW
    ages = {**FRESH, Source.EXOPLANET_EU: 200.0}
    assert classify(9.9, None, [], [], ages, CFG).match_class == MatchClass.UNVERIFIED
    ages = {**FRESH, Source.TOI: 49.0}
    assert classify(9.9, None, [], [], ages, CFG).match_class == MatchClass.UNVERIFIED
    assert CFG.stale_sources({**FRESH, Source.PUB_DTARPS: None}) == ["pub_dtarps"]


def test_confirmed_planet_beats_eb_catalog_entry():
    """Sector 69 regression: confirmed hot Jupiters are also in the TESS EB catalog."""
    host = [_obj(Source.EB_CATALOG, 0.9415, disp="EB"), _obj(Source.ARCHIVE_PLANET, 0.9415)]
    assert classify(0.9415, None, host, [], FRESH, CFG).match_class == MatchClass.KNOWN_PLANET
    host = [_obj(Source.EB_CATALOG, 2.0, disp="EB"), _obj(Source.TOI, 2.0, disp="PC")]
    assert classify(2.0, None, host, [], FRESH, CFG).match_class == MatchClass.KNOWN_TOI
    assert classify(2.0, None, host[:1], [], FRESH, CFG).match_class == MatchClass.KNOWN_FP


def test_host_eb_ignores_eb_rows_that_are_the_hosts_planet():
    """Audit A10 (WASP-173): the EB-catalog row of a hot Jupiter is not a binary host."""
    planet = _obj(Source.ARCHIVE_PLANET, 1.38665, 1000.0, err=1e-6)
    eb_dup = _obj(Source.EB_CATALOG, 1.3867, 1000.0, disp="EB")
    r = classify(5.1, 1001.0, [planet, eb_dup], [], FRESH, CFG)
    assert r.match_class == MatchClass.NEW and not r.host_eb
    eb_real = _obj(Source.EB_CATALOG, 2.9, 1000.0, disp="EB")
    assert classify(5.1, 1001.0, [planet, eb_real], [], FRESH, CFG).host_eb


def test_precedence_collects_transit_matches_before_priority():
    """A confirmed planet found only by transit times beats an EB-catalog period match."""
    b = _obj(Source.ARCHIVE_PLANET, 17.667, 1000.0, name="b", err=1e-4)
    c = _obj(Source.ARCHIVE_PLANET, 29.797, 1005.0, name="c", err=1e-4)
    t_b = 1000.0 + 100 * 17.667
    t_c = 1005.0 + 59 * 29.797
    p = abs(t_c - t_b)
    eb = _obj(Source.EB_CATALOG, p, None, disp="EB", name="eb")
    r = classify(p, t_b, [eb, b, c], [], FRESH, CFG, transit_times=[t_b, t_c], duration_days=0.12)
    assert r.match_class == MatchClass.KNOWN_PLANET and r.match_type == "transit_times"
    assert {o.name for o, _ in r.matched} == {"b", "c", "eb"}


# ---------------------------------------------------------------- A9: transit by transit


def test_transits_of_different_known_planets_are_not_a_new_planet():
    """HD 23472 regression: 1 transit of b (17.67 d) + 1 of c (29.80 d) became "P = 10.29 d"."""
    b = KnownObject(Source.ARCHIVE_PLANET, "b", 1, 17.667, t0_btjd=1000.0, period_err_days=1e-4)
    c = KnownObject(Source.ARCHIVE_PLANET, "c", 1, 29.797, t0_btjd=1005.0, period_err_days=1e-4)
    t_b = 1000.0 + 100 * 17.667
    t_c = 1005.0 + 59 * 29.797
    r = classify(
        abs(t_c - t_b),
        t_b,
        [b, c],
        [],
        FRESH,
        CFG,
        transit_times=[t_b, t_c],
        duration_days=0.12,
    )
    assert r.match_class == MatchClass.KNOWN_PLANET and r.match_type == "transit_times"
    assert {o.name for o, _ in r.matched} == {"b", "c"}
    assert r.phase_checked


def test_new_planet_transits_not_explained_stay_new():
    b = KnownObject(Source.ARCHIVE_PLANET, "b", 1, 17.667, t0_btjd=1000.0, period_err_days=1e-4)
    r = classify(
        5.3, 1003.0, [b], [], FRESH, CFG, transit_times=[1003.0, 1008.3, 1013.6], duration_days=0.1
    )
    assert r.match_class == MatchClass.NEW and r.host_known


def test_stale_ephemeris_is_ignored_for_transit_matching():
    """3 sigma_prop > min(0.25 d, 0.1 P): the ephemeris cannot explain transits."""
    b = KnownObject(Source.TOI, "b", 1, 10.0, t0_btjd=0.0, period_err_days=0.01, disposition="PC")
    r = classify(
        7.0, 3000.0, [b], [], FRESH, CFG, transit_times=[3000.0, 3007.0], duration_days=0.1
    )
    assert r.match_class == MatchClass.NEW


def test_secondary_phase_allowed_for_candidates_not_for_confirmed_planets():
    """Signal 1718 (primary + secondary of a CTOI), with a precise ephemeris.

    The stored CTOI-34040424.01 ephemeris (sigma_P 0.002 d, 87 cycles: 3 sigma = 0.52 d) is
    now too uncertain to test, so that exact case is no longer matched by transit times.
    """
    kw = dict(t0_btjd=1372.6088, period_err_days=2e-5)
    ctoi = KnownObject(Source.CTOI, "CTOI", 1, 20.8564, disposition="PC", **kw)
    planet = KnownObject(Source.ARCHIVE_PLANET, "pl", 1, 20.8564, **kw)
    t1 = 1372.6088 + 87 * 20.8564
    t2 = t1 + 0.5 * 20.8564
    tts = [t1, t2]
    r = classify(9.30089, t1, [ctoi], [], FRESH, CFG, transit_times=tts, duration_days=0.12)
    assert r.match_class == MatchClass.KNOWN_CTOI and r.match_type == "transit_times"
    # a confirmed planet only explains t1 (phase 0): 1 of 2 with coverage ~0.01 is enough...
    ev = explain_transits(tts, 0.12, [planet], CFG)
    assert [bool(h) for h in ev.per_transit] == [True, False]
    # ...but the second transit is never attributed to a planet's "secondary"
    ev = explain_transits(tts, 0.12, [ctoi], CFG)
    assert [bool(h) for h in ev.per_transit] == [True, True]
    stale = KnownObject(Source.CTOI, "C", 1, 20.8564, t0_btjd=1372.6088, period_err_days=0.002)
    r = classify(9.30089, t1, [stale], [], FRESH, CFG, transit_times=tts, duration_days=0.12)
    assert r.match_class == MatchClass.NEW and r.host_known


def test_short_period_known_object_does_not_explain_transits_by_chance():
    """Audit A9: the old matcher fired by chance 80-87 % of the time for known P < 2 d."""
    toi = KnownObject(Source.TOI, "short", 1, 0.6, t0_btjd=3000.0, period_err_days=1e-6)
    # both transits "explained" (phase 0 and 0.5), but the windows cover 28 % of the orbit
    tts = [3000.0 + 0.6 * 10 + 0.035, 3000.0 + 0.6 * 25 + 0.33]
    ev = explain_transits(tts, 0.08, [toi], CFG)
    assert ev.k == 2 and ev.coverage > 0.25 and ev.fap > CFG.transit_max_fap
    r = classify(9.03, tts[0], [toi], [], FRESH, CFG, transit_times=tts, duration_days=0.08)
    assert r.match_class == MatchClass.NEW


def test_every_object_explaining_a_transit_is_collected():
    a = KnownObject(
        Source.TOI, "a", 1, 10.0, t0_btjd=3000.0, period_err_days=1e-6, disposition="PC"
    )
    b = KnownObject(Source.CTOI, "b", 1, 15.0, t0_btjd=3000.0, period_err_days=1e-6)
    ev = explain_transits([3030.0, 3045.0], 0.1, [a, b], CFG)
    assert {o.name for o in ev.per_transit[0]} == {"a", "b"}


def test_binomial_sf():
    assert binom_sf(0, 5, 0.3) == 1.0
    assert binom_sf(2, 2, 0.1) == pytest.approx(0.01)
    assert binom_sf(1, 2, 0.1) == pytest.approx(0.19)


def test_host_eb_flag():
    eb = KnownObject(Source.EB_CATALOG, "EB", 1, 22.57, t0_btjd=1337.9, disposition="EB")
    r = classify(
        6.354, 3182.7, [eb], [], FRESH, CFG, transit_times=[3182.69, 3201.76], duration_days=0.024
    )
    assert r.host_eb


def test_nearby_known_object_flags_contamination():
    near = [_obj(Source.TOI, 3.7, disp="PC", sep=45.0)]
    r = classify(3.7, None, [], near, FRESH, CFG)
    assert r.match_class == MatchClass.NEARBY_KNOWN and not r.host_known


# ---------------------------------------------------------------- integer harmonics (G7)


def test_integer_harmonic_of_short_period_toi_on_host():
    """TOI-4981.01-like: the candidate is found at 4x a short-period TOI."""
    toi = _obj(Source.TOI, 0.45, 3000.0, disp="PC", err=1e-6, name="short")
    p = 4 * 0.45 * (1 + 2e-4)
    r = classify(
        p, 3000.0 + 40 * 0.45, [toi], [], FRESH, CFG, duration_days=0.04, period_err_days=1e-4
    )
    assert r.match_class == MatchClass.KNOWN_TOI and r.match_type == "harmonic"
    assert r.matched[0][1].alias == Fraction(4)
    # same period, wrong phase: not the same object
    r = classify(
        p, 3000.0 + 40 * 0.45 + 0.2, [toi], [], FRESH, CFG, duration_days=0.04, period_err_days=1e-4
    )
    assert r.match_class == MatchClass.NEW
    # harmonics are matched on the host only
    far = _obj(Source.TOI, 0.45, 3000.0, disp="PC", err=1e-6, sep=60.0)
    r = classify(
        p, 3000.0 + 40 * 0.45, [], [far], FRESH, CFG, duration_days=0.04, period_err_days=1e-4
    )
    assert r.match_class == MatchClass.NEW


def test_high_harmonic_of_ultra_short_period_object():
    """WD 0137-349 b-like: P = 0.0803 d found at 8x by a search with P_min = 0.5 d."""
    wd = _obj(Source.ARCHIVE_PLANET, 0.0803, 3000.0, err=1e-7, name="WD b")
    p = 8 * 0.0803
    r = classify(
        p, 3000.0 + 300 * 0.0803, [wd], [], FRESH, CFG, duration_days=0.01, period_err_days=5e-5
    )
    assert r.match_class == MatchClass.KNOWN_PLANET and r.match_type == "harmonic"


def test_half_integer_harmonic_for_binaries_only():
    eb = _obj(Source.EB_CATALOG, 1.0, 3000.0, disp="EB", err=1e-6)
    r = classify(3.5, 3000.0 + 7.5, [eb], [], FRESH, CFG, duration_days=0.05, period_err_days=1e-4)
    assert r.match_class == MatchClass.KNOWN_FP and r.matched[0][1].alias == Fraction(7, 2)
    pl = _obj(Source.ARCHIVE_PLANET, 1.0, 3000.0, err=1e-6)
    r = classify(3.5, 3000.0 + 7.5, [pl], [], FRESH, CFG, duration_days=0.05, period_err_days=1e-4)
    assert r.match_class == MatchClass.NEW


def test_harmonic_with_imprecise_period_is_not_a_match():
    """With a 1 % period error, some n in 4..50 is always close: no evidence, no match."""
    toi = _obj(Source.TOI, 0.31, 3000.0, disp="PC", err=1e-6)
    p = 23 * 0.31
    r = classify(
        p,
        3000.0 + 23 * 0.31 * 5,
        [toi],
        [],
        FRESH,
        CFG,
        duration_days=0.1,
        period_err_days=0.01 * p,
    )
    assert r.match_class == MatchClass.NEW


# ---------------------------------------------------------------- period-less TOIs (B9)


def test_periodless_toi_matched_by_epoch_or_flagged():
    single = _obj(Source.TOI, None, 3010.0, disp="PC", name="TOI-single")
    r = classify(5.0, 3000.0, [single], [], FRESH, CFG, duration_days=0.1, period_err_days=1e-3)
    assert r.match_class == MatchClass.KNOWN_TOI and r.match_type == "epoch"
    r = classify(5.0, 3001.0, [single], [], FRESH, CFG, duration_days=0.1, period_err_days=1e-3)
    assert r.match_class == MatchClass.NEW and any(PERIODLESS_TOKEN in n for n in r.notes)
    no_epoch = _obj(Source.CTOI, None, None, disp="PC")
    r = classify(5.0, 3001.0, [no_epoch], [], FRESH, CFG, duration_days=0.1)
    assert r.match_class == MatchClass.NEW and any(PERIODLESS_TOKEN in n for n in r.notes)
    imaged = _obj(Source.EXOPLANET_EU, None, None, disp="CP")  # direct imaging: no transit
    r = classify(5.0, 3001.0, [imaged], [], FRESH, CFG, duration_days=0.1)
    assert not any(PERIODLESS_TOKEN in n for n in r.notes)


# ---------------------------------------------------------------- star selection (batch)


def test_proper_motion_track_matches_position_only_catalogs():
    """A 2"/yr star: an exoplanet.eu position at the observation epoch is 50" from J2000."""
    from planethunter.crossmatch.batch import KnownCatalog, btjd_to_jyear, select_objects

    t_obs = 3300.0
    dt = btjd_to_jyear(t_obs) - 2000.0
    ra, dec = 150.0, 10.0
    off_deg = 2.0 * dt / 3600.0  # pmdec = 2000 mas/yr
    known = pd.DataFrame(
        {
            "source": [Source.EXOPLANET_EU.value],
            "name": ["eu b"],
            "tic_id": pd.array([pd.NA], dtype="Int64"),
            "ra_deg": [ra],
            "dec_deg": [dec + off_deg],
            "period_days": [3.0],
            "period_err_days": [np.nan],
            "t0_btjd": [np.nan],
            "disposition": ["CP"],
        }
    )
    cat = KnownCatalog(known)
    host, near = select_objects(cat, 7, ra, dec, CFG)
    assert not host and near  # ~50" without proper motion
    host, _ = select_objects(
        cat, 7, ra, dec, CFG, pmra_mas_yr=0.0, pmdec_mas_yr=2000.0, t_obs_btjd=t_obs
    )
    assert host and host[0].separation_arcsec < 1.0
    host, _ = select_objects(cat, 7, None, None, CFG)
    assert not host


def test_exact_tic_id_match_is_host_even_without_position():
    from planethunter.crossmatch.batch import KnownCatalog, select_objects

    known = pd.DataFrame(
        {
            "source": [Source.TOI.value],
            "name": ["TOI-1.01"],
            "tic_id": pd.array([42], dtype="Int64"),
            "ra_deg": [np.nan],
            "dec_deg": [np.nan],
            "period_days": [3.0],
            "period_err_days": [np.nan],
            "t0_btjd": [np.nan],
            "disposition": ["PC"],
        }
    )
    host, near = select_objects(KnownCatalog(known), 42, None, None, CFG)
    assert [o.name for o in host] == ["TOI-1.01"] and host[0].separation_arcsec == 0.0


def test_marginal_transit_coincidence_is_flagged_not_known():
    """Sector 69 GJ 143 (signal 2129): 1 of 2 transits on GJ 143 b, chance ~0.04."""
    b = KnownObject(Source.ARCHIVE_PLANET, "GJ 143 b", 1, 35.61344, 1000.0, 1.6e-5)
    c = KnownObject(Source.ARCHIVE_PLANET, "GJ 143 c", 1, 7.78979, 1001.0, 1.3e-5)
    t_b = 1000.0 + 60 * 35.61344 + 0.03
    tts = [t_b - 17.6, t_b]
    r = classify(17.6, tts[0], [b, c], [], FRESH, CFG, transit_times=tts, duration_days=0.033)
    assert r.match_class == MatchClass.NEW
    assert any(n.startswith(PARTIAL_TRANSIT_TOKEN) for n in r.notes)
    # nothing near any known ephemeris: no token
    far = [1003.3, 1020.9]
    r = classify(17.6, far[0], [b, c], [], FRESH, CFG, transit_times=far, duration_days=0.033)
    assert not any(PARTIAL_TRANSIT_TOKEN in n for n in r.notes)


# ---------------------------------------------------------------- run-level flags (A8)


def _run(n_bg=150, n_spike=30, seed=0, t_spike=1010.1, t_spike2=1018.6, spike_hits=2):
    """Synthetic run: n_bg targets with 2 random transits, n_spike targets with `spike_hits`
    transits at common epochs (spacecraft systematics: t_spike, then t_spike2) and the rest
    random."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_bg + n_spike):
        t = rng.uniform(1000.0, 1027.0, 2)
        if i >= n_bg:
            t[0] = t_spike + rng.normal(0, 0.02)
            if spike_hits >= 2:
                t[1] = t_spike2 + rng.normal(0, 0.02)
        rows.append(
            dict(
                signal_id=i + 1,
                tic_id=1000 + i,
                transit_times_json=str([float(x) for x in sorted(t)]),
                period_days=abs(t[1] - t[0]),
                period_err_days=1e-3,
                t0_btjd=float(min(t)),
                duration_hours=2.0,
                depth_ppm=1000.0,
                ra_deg=10.0 + i,  # 1 deg apart: no shared signals
                dec_deg=0.0,
                tmag=10.0,
            )
        )
    return pd.DataFrame(rows)


def test_epoch_spikes_flag_common_epoch_systematics():
    from planethunter.crossmatch.runlevel import epoch_spikes

    sigs = _run()
    frac, spikes = epoch_spikes(sigs, CFG)
    assert len(spikes) >= 1
    assert ((spikes.t_start <= 1010.1) & (spikes.t_end > 1010.1)).any()
    spiky = frac[sigs.signal_id[sigs.tic_id >= 1150]]
    background = frac[sigs.signal_id[sigs.tic_id < 1150]]
    assert (spiky >= CFG.epoch_spike_max_frac).mean() > 0.9
    assert (background >= CFG.epoch_spike_max_frac).mean() < 0.05


def test_epoch_spike_single_hit_does_not_flag():
    """One transit on a spike is not enough (a real 2-transit planet can be unlucky)."""
    from planethunter.crossmatch.runlevel import epoch_spikes

    sigs = _run(spike_hits=1)
    frac, spikes = epoch_spikes(sigs, CFG)
    assert ((spikes.t_start <= 1010.1) & (spikes.t_end > 1010.1)).any()
    assert (frac[sigs.signal_id[sigs.tic_id >= 1150]] == 0.0).all()


def test_epoch_spikes_need_many_targets_and_ignore_own_target():
    from planethunter.crossmatch.runlevel import epoch_spikes

    frac, spikes = epoch_spikes(_run(n_bg=40, n_spike=10), CFG)
    assert frac.isna().all() and spikes.empty  # < epoch_spike_min_targets: no statistics
    sigs = _run(n_spike=0)
    # one target with many signals at the same epoch does not create a spike by itself
    extra = pd.DataFrame(
        [
            dict(signal_id=9000 + k, tic_id=5, transit_times_json="[1015.05, 1022.0]")
            for k in range(40)
        ]
    )
    frac, spikes = epoch_spikes(pd.concat([sigs, extra], ignore_index=True), CFG)
    assert not ((spikes.t_start <= 1015.05) & (spikes.t_end > 1015.05)).any()
    assert frac[9000] < 0.5


def _pair(sep_arcsec, depth_a, tmag_a, depth_b, tmag_b, p_b=5.0, t0_b=1001.0):
    common = dict(period_err_days=1e-3, duration_hours=2.0, ra_deg=50.0)
    return pd.DataFrame(
        [
            dict(
                signal_id=1,
                tic_id=11,
                period_days=5.0,
                t0_btjd=1001.0,
                depth_ppm=depth_a,
                dec_deg=0.0,
                tmag=tmag_a,
                transit_times_json="[1001.0, 1006.0]",
                **common,
            ),
            dict(
                signal_id=2,
                tic_id=22,
                period_days=p_b,
                t0_btjd=t0_b,
                depth_ppm=depth_b,
                dec_deg=sep_arcsec / 3600.0,
                tmag=tmag_b,
                transit_times_json="[1001.0, 1006.0]",
                **common,
            ),
        ]
    )


def _roles(df):
    from planethunter.crossmatch.runlevel import shared_signals

    sh = shared_signals(df, CFG).set_index("signal_id")
    return {int(k): v for k, v in sh["shared_signal_role"].items()}, sh


def test_shared_signal_duplicate_and_source_victim():
    roles, sh = _roles(_pair(1.0, 1000, 10.0, 1100, 10.1))
    assert roles == {1: "duplicate", 2: "duplicate"}
    assert sh.loc[1, "shared_signal_tic"] == 22 and sh.loc[1, "shared_signal_sep_arcsec"] < 1.1
    # 30": the bright star with the larger eclipsed flux (depth x flux) is the source
    roles, _ = _roles(_pair(30.0, 1000, 10.0, 2000, 12.0))
    assert roles == {1: "source", 2: "victim"}
    # within one pixel, comparable flux: the larger one is still the source
    roles, _ = _roles(_pair(10.0, 1000, 10.0, 1500, 10.6))
    assert roles == {1: "source", 2: "victim"}


def test_shared_signal_comparable_flux_far_apart_means_third_star():
    roles, sh = _roles(_pair(60.0, 1000, 10.0, 1500, 10.6))
    assert roles == {1: "victim", 2: "victim"}
    assert "third star" in sh.loc[1, "shared_signal_note"]


def test_shared_signal_aliases_and_non_matches():
    roles, _ = _roles(_pair(30.0, 1000, 10.0, 200, 12.0, p_b=10.0, t0_b=1006.0))  # 2P, on grid
    assert roles == {1: "source", 2: "victim"}
    roles, _ = _roles(_pair(30.0, 1000, 10.0, 200, 12.0, p_b=10.0, t0_b=1003.5))  # off grid
    assert roles == {}
    roles, _ = _roles(_pair(30.0, 1000, 10.0, 200, 12.0, p_b=5.3))  # different period
    assert roles == {}
    roles, _ = _roles(_pair(200.0, 1000, 10.0, 200, 12.0))  # beyond 120"
    assert roles == {}


def test_shared_signal_missing_tmag_is_source_with_note():
    roles, sh = _roles(_pair(30.0, 1000, 10.0, 2000, np.nan))
    assert roles[1] == "source" and "undetermined" in sh.loc[1, "shared_signal_note"]


def test_run_level_flags_one_row_per_signal():
    from planethunter.crossmatch.runlevel import run_level_flags

    dup = _pair(1.0, 1000, 10.0, 1000, 10.0).assign(signal_id=[901, 902], tic_id=[1, 2])
    sigs = pd.concat([_run(), dup], ignore_index=True)
    out = run_level_flags(sigs, CFG)
    assert len(out) == len(sigs) and set(out.columns) >= {
        "epoch_spike_frac",
        "shared_signal_tic",
        "shared_signal_sep_arcsec",
        "shared_signal_role",
    }
    assert out.set_index("signal_id").loc[901, "shared_signal_role"] == "duplicate"


# ---------------------------------------------------------------- send-time gate (A1)


def _write_mirrors(root, rows_by_source, *, stamp=None):
    from datetime import UTC, datetime

    from planethunter.catalogs.mirrors import COLUMNS, mirror_dir

    ts = stamp or f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    for source in Source:
        df = pd.DataFrame(rows_by_source.get(source, []), columns=COLUMNS)
        df["tic_id"] = df["tic_id"].astype("Int64")
        d = mirror_dir(root, source)
        d.mkdir(parents=True, exist_ok=True)
        df.to_parquet(d / f"{ts}.parquet", index=False)


def _seed_candidates(root):
    from planethunter.db.store import connect, insert_df

    con = connect(root)
    targets = {
        "tic_id": [100, 200],
        "ra_deg": [10.0, 50.0],
        "dec_deg": [0.0, 0.0],
        "tmag": [9.5, 9.8],
        "radius_rsun": [1.0, 1.0],
    }
    insert_df(con, "targets", pd.DataFrame(targets))
    signals = {
        "signal_id": [1, 2],
        "run_id": ["r", "r"],
        "tic_id": [100, 200],
        "sectors": ["1", "1"],
        "period_days": [5.3, 7.1],
        "period_err_days": [1e-3, 1e-3],
        "t0_btjd": [1327.0, 1328.0],
        "duration_hours": [3.0, 3.0],
        "depth_ppm": [2000.0, 2000.0],
        "sde": [20.0, 20.0],
        "snr": [20.0, 20.0],
        "n_transits": [4, 3],
        "transit_times_json": [str([1327.0 + 5.3 * k for k in range(4)]), None],
    }
    insert_df(con, "signals", pd.DataFrame(signals))
    vetting = {
        "signal_id": [1, 2],
        "verdict": ["PASS_BASIC"] * 2,
        "score": [0.9, 0.9],
        "fit_depth_ppm": [2000.0, 2000.0],
        "fit_t14_hours": [3.0, 3.0],
        "p_planet": [0.9, 0.9],
        "failed": ["", ""],
    }
    insert_df(con, "vetting", pd.DataFrame(vetting))
    xm = {"signal_id": [1, 2], "match_class": ["NEW", "NEW"], "host_known": [False, False]}
    insert_df(con, "crossmatch", pd.DataFrame(xm))
    cands = {
        "signal_id": [1, 2],
        "tic_id": [100, 200],
        "run_id": ["r", "r"],
        "match_class": ["NEW", "NEW"],
        "verdict": ["PASS_BASIC"] * 2,
        "score": [0.9, 0.9],
        "severity": ["P1", "P1"],
        "review_status": ["pending", "pending"],
    }
    insert_df(con, "candidates", pd.DataFrame(cands))
    con.close()


def test_send_time_recheck_blocks_host_that_got_a_toi(tmp_path):
    """A1: the host got a TOI after the batch crossmatch -> the alert is not sent."""
    from datetime import UTC, datetime

    from planethunter.alerts.notify import send_alerts
    from planethunter.config import Config
    from planethunter.db.store import connect

    _seed_candidates(tmp_path)
    toi = dict(
        source=Source.TOI.value,
        name="TOI-9999.01",
        tic_id=100,
        ra_deg=10.0,
        dec_deg=0.0,
        period_days=5.3,
        period_err_days=1e-4,
        t0_btjd=1327.0,
        depth_ppm=2000.0,
        disposition="PC",
        synced_at="x",
    )
    _write_mirrors(tmp_path, {Source.TOI: [toi]})
    out = {o.signal_id: o for o in send_alerts(tmp_path, Config(), "r", dry_run=True)}
    assert out[1].status == "skipped" and "KNOWN_TOI" in out[1].reason
    assert out[2].status == "dry_run"
    con = connect(tmp_path)
    cls, name, checked = con.execute(
        "SELECT match_class, matched_name, checked_at FROM crossmatch WHERE signal_id = 1"
    ).fetchone()
    sent = con.execute("SELECT signal_id, message FROM alerts").fetchall()
    con.close()
    assert cls == "KNOWN_TOI" and name == "TOI-9999.01"
    assert abs((datetime.now(UTC).replace(tzinfo=None) - checked).total_seconds()) < 120  # UTC
    assert [s for s, _ in sent] == [2] and "re-checked at send time" in sent[0][1]


def test_send_time_gate_refuses_with_stale_mirrors(tmp_path):
    from planethunter.alerts.notify import send_alerts
    from planethunter.config import Config

    _seed_candidates(tmp_path)
    _write_mirrors(tmp_path, {}, stamp="20200101T000000Z")
    out = send_alerts(tmp_path, Config(), "r", dry_run=True)
    assert {o.status for o in out} == {"skipped"} and all("stale" in o.reason for o in out)
