# Rerun after the 2026-10-10 code audit (sectors 69 and 107)

Before/after measurement for the fixes in [PLAN §17](../PLAN.md). "Before" is the code as of 2026-10-09 ([sector 69 vetting](2026-10-09-s0069-vetting.md), [sector 107 run](2026-10-09-s0107-run.md)). "After" is the code as of 2026-10-13, with `PLANETHUNTER_MAX_WORKERS=6`.

| Run | run_id | Targets | Signals (SDE ≥ 7) | Errors |
|---|---|---|---|---|
| Recall benchmark, s69 | `20261010T063105Z-single-s69` | 173 | 204 | 0 |
| Sector 69 | `20261010T063429Z-single-s69` | 2168 | 1448 | 2 (MemoryError) |
| Null, inverted flux, s69 | `20261010T064409Z-single-null-inverted-s69` | 2168 | 1240 | 0 |
| Null, scrambled orbits, s69 | `20261013T045733Z-single-null-scrambled-s69` | 2168 | 1280 | 0 |
| Sector 107 | `20261013T051603Z-single-s107` | 12 998 | 8968 (was 4431) | 0 |

Sector 107 has twice as many signals because the period range now follows the QLP rule: P_min at a = 2R\*, P_max = 0.9 × span instead of span/2.

## 1. Search recall (sector 69 benchmark)

| | Before | After |
|---|---|---|
| Recall on detectable TOIs (P 1, 2, 1/2 with phase) | 123/135 = 91.1 % | **123/135 = 91.1 %** |
| Recall, all TOIs with data | — | 126/185 = 68.1 % |

There is no regression. Report: [2026-10-10-s0069-nogit.md](2026-10-10-s0069-nogit.md). Durations now match the catalog: median ratio to the TOI duration is 1.04, against 0.88 before, now that the TLS fill-factor bias is removed.

## 2. Empirical false-alarm rate (null runs, Thompson et al. 2018)

On sector 69, 2168 targets:

| | Real | Inverted flux | Scrambled orbits |
|---|---|---|---|
| Signals with SDE ≥ 9 | 643 | 558 | 523 |
| Passing basic vetting | 152 | 55 | 99 |

- **The SDE cut lets noise through.** SDE ≥ 9 passes about 0.25 noise signals per target. The white-noise figure "SDE 9 ≈ 10⁻⁴" (TLS docs) is optimistic by orders of magnitude on real light curves, as Pont et al. 2006 predicts for red noise.
- **Basic vetting removes 82–90 % of them.** The false alarms that survive are comparable in number to the real signals that pass. The ML ranking does the rest: only 1–2 % of null signals reach the P1 cut (section 4).
- **Caveat.** Inverted deep transits leave dips on their flanks after detrending, and scrambling keeps transits that fall within one orbit. Both runs therefore over-count noise somewhat; they are upper bounds.

## 3. Basic vetting by known class

| Class | s69 before | s69 after | s107 before | s107 after |
|---|---|---|---|---|
| KNOWN_PLANET pass | 44/57 (77 %) | **41/58 (71 %)** | 66/84 (79 %) | **75/92 (82 %)** |
| TFOPWG FP / EB pass | 7/65 (11 %) | **4/66 (6 %)** | 7/132 (5 %) | **15/142 (11 %)** |
| KNOWN_TOI pass | 66/80 | 65/83 (78 %) | 77/104 | 64/105 (61 %) |
| NEW pass | 11/237 | 42/430 | 62/1339 | 212/2805 |

Classes changed between runs: the crossmatch is stricter, and new EB and published-candidate mirrors were added. The columns therefore compare different samples.

**s69 planets, −6 points.**
- 6 confirmed planets are vetoed by SNR < 7.1. Their SNR was already below 7.1 in the old run (TOI-238 c 6.6, TOI-209 b 6.8, TOI-4405 b 6.4, TOI-205 b 6.8), so the veto is not new.
- 2 fail on `shape` plus `kdr25_grazing`: LTT 9779 b and HIP 65 A b, both grazing.
- During the rerun, counting `snr_pink` as a soft fail cost 2 more planets and 4 TOIs, with no FP gain. It now lowers the score only (`vetting.uncounted_soft_tests`).

**s107 FP, +6 points.** Most of the FPs that pass are eclipsing binaries detected at half or twice their period, at 0.1–2 % depth (diluted), plus a few shallow TOI false positives. Flux-only tests cannot reject diluted binaries; the difference image in deep vetting is the stage that does (section 6).

**s107 TOIs.** The pass rate drops mostly on `kdr25_grazing` (33) and `shape` (30), the grazing geometries the limb-darkened fit now detects. TOIs are not all planets.

## 4. Calibrated ranking (`p_rank`, schema 2)

Training data: s69 + s107 known classes, plus null-run signals as negatives.

| | Value |
|---|---|
| Nested out-of-fold ROC-AUC, model vs score | 0.960 vs 0.867 |
| PR-AUC, model vs score | 0.785 vs 0.669 |
| Brier | 0.039 |
| C (grouped grid) | 0.3 |
| P2 cut (90 % recall on known planets) | 0.132, FPR 9.5 % |
| P1 cut (FPR ≤ 1 % but ≥ 70 % recall) | 0.477, recall 70 %, FPR 2.1 % |

| Negative source | n | ≥ P2 cut | ≥ P1 cut |
|---|---|---|---|
| EB catalog | 162 | 9 % | 2 % |
| TFOPWG FP | 46 | 24 % | 4 % |
| Null, inverted | 558 | 7 % | 1 % |
| Null, scrambled | 522 | 11 % | 2 % |

Known planets treated as NEW, without deep vetting:

| | ≥ P2 | P1 |
|---|---|---|
| With the ML | 85 % | 49 % |
| Without the ML | 77 % | 59 % |

For negatives, P1 drops from 2.6 % to 0.3 %. The ML only lowers priority: planets that miss P1 stay in the review queue.

## 5. Run-level systematics (`NEW` signals flagged)

| | s69 | s107 |
|---|---|---|
| Epoch spikes (≥ 2 transits in spikes, ≥ 50 % of transits) | 83 | 171 |
| Shared signal, victim | 6 | 110 |
| Shared signal, duplicate (TIC split, ≤ 2″) | 0 | 27 |
| Shared signal, source (capped at P2) | 4 | 96 |

**The epoch-spike threshold was changed during this rerun.** The audit's rule, 5 × the median count per bin, found no spike in the new sector 107: the background rose to about 100 targets per bin, while the spikes (BTJD 4268.75, 4276.0, 4283.75, …) stood 3.5× and 25σ above it. The rule is now median + 6 × robust MAD, at least 2 × the median, and at least 2 transits inside spikes, so that one unlucky transit does not suppress a real 2-transit planet.

| | Spike bins | NEW flagged | Known planets/TOIs flagged |
|---|---|---|---|
| s107, new rule | 6 | 171 | 0 of 216 |
| s107, old rule | 0 | 0 | 0 |
| s69, new rule | 12 | 83 | 2 of 152 |
| s69, old rule | 9 | 399 | 5 of 152 |

## 6. Candidates and deep vetting (sector 107)

**After basic vetting, crossmatch flags and the ML:** P1 = 2, P2 = 239 (sector 69: P2 = 43). Deep vetting runs on the 241 candidates; its results will be added to this section when it finishes.

| signal | TIC | P (d) | Depth (ppm) | Rp (R⊕) | R\* (R☉) | Tmag | p_rank | Notes |
|---|---|---|---|---|---|---|---|---|
| 10793 | 594723 | 2.0515 | 15 500 | 15.3 | 1.19 | 13.1 | 0.55 | Hot-Jupiter-like; all basic tests pass; secondary 7 % of primary at 2.4σ (not significant) |
| 13981 | 121634766 | 0.1790 (found at 0.358, halved) | 17 150 | 4.5 | 0.28 (Teff 2928 K) | 14.7 | 0.86 | Ultra-short period on an M dwarf; could also be a diluted binary. Shape τ/T14 0.344 sits at the 0.35 limit |

Both are signals for human review, not discoveries.
