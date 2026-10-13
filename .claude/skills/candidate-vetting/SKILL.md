---
name: candidate-vetting
description: Checklist of the 13 exoplanet candidate vetting tests with formulas, thresholds and code (odd-even, secondary, shape, radius, duration vs stellar density, TPF centroid, Gaia neighbors, momentum dumps, multi-sector, triceratops FPP). Use when implementing, reviewing or interpreting the vetting of a signal.
---

# Candidate vetting

Each test returns `TestResult(name, value, threshold, passed, veto, note, extra)`. Missing data → `passed=None`, never an exception. `extra` holds machine-readable details (e.g. FPP validation-region flags).

| # | Test | Threshold | Vetoes on its own? |
|---|---|---|---|
| 1 | SDE | ≥ 9 | yes (detection gate) |
| 2 | SNR | ≥ 7.1 | yes (detection gate) |
| 2b | S/N_pink | ≥ 9 (QLP) | configurable (`vetting.snr_pink_veto`); NULL in old runs → no data, never a veto |
| 3 | n transits | ≥ 2 (1 → mono) | yes (detection gate) |
| 4 | odd-even | z < 3 | yes if z > 5 |
| 5 | secondary | < 3σ | yes if > 5σ and ≥ 10 % of primary; same depth/duration → re-vet at P/2 |
| 6 | shape | Rp/R* < 0.3, τ/T14 ≤ 0.35 (trapezoid) | no (hard fail) |
| 6b | kdr25_grazing | k + b ≤ 1.04 (batman LD fit) | no (soft, weight 0.6) |
| 7 | radius | Rp < 2 R_Jup | yes if Rp > 3 R_Jup, reliable R* and another EB sign |
| 8 | duration | 0.15 ≤ T_obs/T_pred ≤ 1.67 | no |
| 9 | centroid | < 1 px from target (3σ) | no (TPF: hard fail) |
| 10 | Gaia neighbors | no neighbor explains it | no |
| 11 | momentum dumps | ≤ 50 % of transits | no |
| 12 | multi-sector | reappears; Δdepth within 2× | yes if absent in ≥ 2 decisive sectors |
| 13 | FPP | < 0.5 and NFPP ≤ 0.1 (< 0.015 / < 1e-3 validation) | yes if NFPP > 0.5 (hard fail otherwise) |

## Verdict and score

- **Verdict:** FAIL on any veto, on any failure of a test in `vetting.hard_fail_tests`, or on more than `vetting.max_soft_fails` (1) soft failures. Otherwise PASS_BASIC.
- **Hard fail tests (default):** `tpf_difference_image`, `fpp_triceratops`, `secondary_scan`, `shape`.
- **Score:** the product of the weights of the failed tests, times `unknown_weight` for each test without data. It is 0 on a veto and is used only for ranking.
- Measured on 2026-10-10 (recompute of s107 / s69; KNOWN_PLANET / KNOWN_FP pass rates):
  - Old rule (score ≥ 0.5): 79 / 5 % and 77 / 11 %.
  - Current setting: 85 / 5 % and 74 / 8 %.
  - `max_soft_fails=1` without the morphology tests as hard fails: 88 / 14 % and 81 / 15 %.
- Measured on 2026-10-10 for the batman fit + kdr25_grazing + soft snr_pink (recompute of the known classes of s107 + s69, 141 KNOWN_PLANET, 197 KNOWN_FP):
  - LD fit + kdr25_grazing: KNOWN_PLANET 112 → 112 pass, KNOWN_FP 15 → 14. The 7 planets failing kdr25 are grazing and already fail `shape` (LTT 9779 b, HIP 65 A b, NGTS-10 b, TOI-263 b, TOI-551.01, TOI-251.01, L 98-59 d).
  - Fitted k / Archive `pl_ratror`: median 1.01 (s107) and 1.00 (s69), against 1.03 for sqrt(trapezoid depth). At low S/N b is poorly constrained (median |b − b_cat| ≈ 0.2).
  - S/N_pink < 9 (estimated, stored runs have NULL): 22 of 141 planets. As a veto it drops 11 of 112 passing planets (10 %), so `snr_pink_veto: false` (soft fail drops 2 planets and 2 FPs). Re-check on a rerun with stored snr_pink.
  - Cost: about 0.2 s per signal (median; mean 0.37 s).

## Formulas

PDCSAP depths are already crowding-corrected (CROWDSAP). For SAP flux: `depth_true = depth_obs / CROWDSAP`.

Radius: `Rp = k * R_star`, k = Rp/R* from the limb-darkened batman fit when it is constrained and not grazing (k + b ≤ 1). Otherwise `k = sqrt(depth)` of the trapezoid: for grazing fits k is degenerate with b, so sqrt(depth) is a lower bound. 1 R_Jup = 11.2 R⊕. `sqrt(depth)` is biased by limb darkening (high by about 5–10 % at low b, low at high b).

Limb-darkened fit (`vetting/ldfit.py::fit_transit_ld`, batman, Kreidberg 2015):
- Quadratic u fixed to the Claret (2017) TESS-band table shipped with TLS (`search/tls.py::tess_limb_darkening`, nearest Teff then log g; Sun-like without Teff).
- Free k, β = b / (1 + k), T14, mid-time; circular orbit, `a² = ((1+k)² − b²) / sin²(π T14 / P) + b²`.
- Supersampling (Kipping 2010b) per cadence group: sub-exposures ≤ `ld_fit_subexposure_minutes` (2-min: 1, 200 s: 2, 10 min: 5, 30 min: 15).
- Three starting b; among solutions within `ld_fit_delta_chi2` (1) of the best χ² the lowest b wins, so a grazing solution must be preferred by the data.
- k on its upper bound (1.0) or T14 on a bound → `unconstrained`: kdr25_grazing gets passed=None and the radius falls back to sqrt(depth).
- Results in `fit` (`ld_k`, `ld_b`, `ld_a_rs`, `ld_t14_hours`, `ld_depth_ppm`; `rp_rs` = the k the radius test used, stored as `vetting.fit_rp_rs`) and in the kdr25_grazing `extra` (also k_err, b_err, u, supersample, center_days).

Radius veto (Mullally et al. 2015): only if R* is reliable (TIC radius and log g ≥ 3.5) and another EB sign exists (V shape, odd-even or secondary failure). Otherwise it is a soft fail.

Odd-even: box depth on odd and even epochs. Errors come from `BlockNoise` (Pont et al. 2006): `z = |d_odd - d_even| / sqrt(s_odd**2 + s_even**2)`.

Secondary at phase 0.5: box of 0.8 T14, with epochs from `floor((t - t0)/P)` so the box is not split. If `|d_sec - d_prim| / σ < 3` and the trapezoid T14 agree within 35 %, it is the in-between transit of a signal found at 2P. The signal is then re-vetted at P/2 with the same t0. The report gets a `period_halved` test (value = P/2) and `report.period_days = P/2`. Deep vetting uses P/2 too. TOI-431 b was vetoed before this rule.

Secondary scan: deepest box dip at phases 0.1–0.9 (5σ). Epochs come from `floor((t - t0)/P - φ + 0.5)`.

Trapezoid: least squares with `soft_l1`, `f_scale = trapezoid_f_scale_sigma × σ_white` (1.0; 0 = plain least squares; known-class results agree within one object). T14 is bounded to 0.2–3 × the search duration. A fit at the upper bound is retried with the duration doubled. A fit still on a bound is unconstrained: the duration test gets `passed=None, value=None` and `fit["t14_at_bound"] = True`.

Predicted duration (circular orbit, b = 0):

```python
rho = M_star / (4 / 3 * np.pi * R_star**3)
a_over_rs = ((G * rho * P**2) / (3 * np.pi)) ** (1 / 3)
T_pred = P / np.pi * np.arcsin((1 + rp_rs) / a_over_rs)
```

The ceiling `T_obs ≤ 1.67 T_pred` follows LEO-Vetter (Kunimoto et al. 2025): eccentric orbits lengthen transits (Kipping 2010). Longer durations point to a blend with a larger star or a wrong R*.

## Centroid (offline, MOM_CENTR)

- **Shift:** per transit, the in-transit mean minus a local linear baseline (1–3 T14 away).
- **Error:** robust scatter of the same estimator at up to 200 fake out-of-transit epochs per sector, never below the white-noise error. White-noise errors failed 2–47 % of random epochs.
- **Sectors:** each sector is evaluated separately (CCD frames differ) and the χ² values are summed.
- **Implied distance:** `D = shift / (CROWDSAP · depth)`.
- **Decision:** fail if the combined significance is ≥ 3σ and D > 1 px.
- **Indeterminate (Kostov et al. 2019):** Tmag < 7 (saturated), or fewer than 3 transits in every sector.

## Difference image (TPF, deep)

```python
diff = out_of_transit.mean(0) - in_transit.mean(0)   # the transit source shines here
c_diff = flux_weighted_centroid(diff, above=0.3 * peak)
tx, ty = tpf.wcs.all_world2pix(*propagate(ra_J2000, dec_J2000, pmra, pmdec, epoch_of_TPF), 0)
offset = hypot(c_diff - (tx, ty))                    # vs CATALOG position (Bryson et al. 2013)
```

- **Fail:** offset > 3σ and > 1 px. σ is the scatter of the per-transit centroids divided by √n.
- **Indeterminate:** with fewer than 3 transits an offset > 1 px is indeterminate.
- **Info:** the offset from the out-of-transit centroid is reported but not used. A bright neighbor pulls it.
- **Proper motion:** TIC positions are J2000. They are propagated linearly to the TPF mid-time (`deep.propagate_position`).

## Gaia neighbors (deep)

The triceratops `calc_depths` formula (Giacalone et al. 2021). For a dilution-corrected (PDCSAP) depth δ, the depth a neighbor would need is:

`δ_nb = δ · F_target,ap / F_nb,ap`, with `F_ap = 10^(-0.4 T) × ∫ Gaussian PSF (σ = 0.75 px) over the aperture pixels`.

- **Positions:** Gaia positions are propagated from 2016.0 to the TPF epoch and projected with the TPF WCS. Without a TPF, a 1.5 px circular aperture is assumed.
- **Magnitudes:** Gaia G is converted to T with Stassun et al. 2019, eq. 1: `T = G − 0.00522555c³ + 0.0891337c² − 0.633923c + 0.0324473`, with c = BP − RP. Without a color, T = G − 0.430.
- **Target match:** the TIC position is propagated to 2016.0. Among sources within 3″, the one whose T is closest to the TIC Tmag wins.
- **Outcomes:**
  - `True`: nothing can produce the dip, or nothing is unresolved.
  - `None` with value = number of plausible unresolved neighbors: needs high-resolution imaging.
  - `None` with value None: error.
  - `False`: the difference image shows a significant offset AND a feasible neighbor lies within max(1 px, 3σ) of the difference centroid. The neighbor IDs are in `extra.at_difference_centroid`.

## Other sectors (deep)

- **Search:** BLS around P and 2P in each other sector.
- **Noise floor:** the 90th percentile of the same BLS at 40 random periods, after masking |phase| < T14 at the best P-equivalent period. Before masking, the floor tracked the signal (SNR 2192 against a floor of 2272).
- **Decisive absence:** expected SNR ≥ 10 and ≥ 1.5 × the floor.

## Momentum dumps and edges

Dump times come from `quality & 32`. A transit with its midpoint < 0.1 d from a dump is flagged. Segment-edge fractions come from the search.

## SIMBAD (deep)

- Fails only on EB\*, SB\* and El\*.
- Variable and young types (current codes, e.g. `Y*O`, `Em*`, `RotV*`) are informational.
- The planet's own entry (`Pl`) is skipped.

## triceratops (tools/fpp/run_fpp.py, isolated env)

```python
target = tr.target(ID=tic_id, sectors=sectors_with_aperture)
assert len(target.pix_coords) == len(apertures)          # a skipped sector misaligns apertures
target.calc_depths(tdepth=depth, all_ap_pixels=apertures, dilution_corrected=True)  # PDCSAP
# ok=False if target.stars row 0 lacks mass/rad/Teff/plx
err0 = max(median(flux_err), 1.4826 * MAD(flux[|phase| > 0.75 T14]))
for _ in range(fpp_repeats):                             # default 3
    target.calc_probs(time=phase, flux_0=flux, flux_err_0=err0, P_orb=P, N=draws,
                      exptime=cadence_days, dilution_corrected=True)
    # ok=False if target.FPP_degenerate
fpp, nfpp = mean(...), mean(...)                         # std reported too
```

**`fpp_test` (Giacalone et al. 2021):**
- FPP ≥ 0.5 fails.
- NFPP > 0.1 fails ("likely nearby false positive").
- NFPP > 0.5 vetoes: most of the posterior sits on a resolved neighbor.
- FPP < 0.015 with NFPP < 1e-3 is the validation level, but only inside the validation region: Rp < 8 R⊕, SNR ≥ 15, 2-min cadence.

**Fields in `extra`:** `in_validation_region`, `rp_ok`, `snr_ok`, `cadence_ok`, `validated`, `likely_planet`, `likely_nearby_fp`, `fpp`, `nfpp`, `fpp_std`, `nfpp_std`, `repeats`. The note contains "outside the validation region" when applicable.

## State in the code (2026-10-10)

**Basic level, no network (`vetting/basic.py::vet_signal`):**
- sde, snr, n_transits: vetoes.
- snr_pink: gate on signals.snr_pink (Pont 2006 on T14); veto if `snr_pink_veto` (default false, see measurement above), else soft (weight 0.5). NULL → passed=None, no unknown_weight (`unknown_exempt_tests`). Scaled with the SNR on period halving.
- independence: veto if masking **stronger** signals removes > 50 % of the transit.
- odd_even.
- secondary, with period halving.
- secondary_scan.
- shape (trapezoid τ/T14, unchanged).
- kdr25_grazing: k + b > 1.04 from the batman fit, soft fail; no data → no unknown_weight.
- radius, with gated veto; k from the batman fit (non-grazing) or sqrt(depth).
- duration: ceiling 1.67; bound-hitting fits are unconstrained.
- centroid: empirical errors, per sector, CROWDSAP.
- edges_dumps.
- consistency.

**Masking weaker siblings (G7):**
- `weaker_signals=` masks weaker sibling signals, except period aliases and echoes.
- It is off in the pipeline (`vetting.mask_weaker_signals: false`). Measured: no planet gained, and 1–2 more EBs passed in s107, because an EB's own eclipses are re-detected at non-alias periods.

**Deep level, network with cache (`vetting/deep.py`, called by `pipeline.run_deep_vetting`):**
- tpf_difference_image, with proper motion.
- gaia_neighbors: VizieR I/355 with BP-RP and proper motion; cache `tic<ID>_v2.parquet`.
- gaia_eb: VizieR I/358/veb, incomplete; source_id kept as an exact int64 string.
- simbad_type.
- other_sectors.
- fpp_triceratops: only for candidates that are still PASS_BASIC.

**FPP:**
- triceratops runs in `tools/fpp`, a separate uv environment (numpy 1.26 / scipy 1.13).
- 1e5 draws take about 6 min per repeat, so 3 repeats take about 18 min.
- Pure helpers (`flux_err_0`, `target_problem`, `summarize`, `compute`) are unit-tested in the main environment with a mock target.

**Same light curve everywhere:** basic vetting (`pipeline._vet_target`), FPP (`pipeline._fpp_for`) and the dossier (`alerts/dossier.py`) re-detrend with `preprocess.signal_windows` + `preprocess.flatten_for_signal` (per-sector search-time windows, ≥ 3 × T14, transits masked at phase 0 and 0.5) at the vetted period (P/2 when `period_halved`). The FPP Rp for the validation region is max(sqrt(depth), fit_rp_rs) × R*.
