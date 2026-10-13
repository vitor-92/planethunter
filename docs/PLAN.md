# PlanetHunter — Exoplanet Search System Plan

> Version 1.2 — 2026-10-13. Living document. Master prompt: [EXPERT_PROMPT.md](EXPERT_PROMPT.md). Rules for Claude Code: [../CLAUDE.md](../CLAUDE.md). Literature basis, with every claim below traceable to a verified reference: [LITERATURE.md](LITERATURE.md).
>
> **v1.1 changes.** The plan now matches the code as of v1.0.0, and was reviewed against the literature. Five corrections:
> - The recall KPI was replaced, because recall on known TOIs is a biased measure.
> - The faint-star niche was redefined (the official FFI products stop at T = 13.5).
> - FPP gates now include NFPP.
> - The CTOI route follows ExoFOP's 2026 publication rule.
> - The gaps found are a prioritized backlog in §17.

## 1. Goal

An autonomous system that, for every new batch of photometric data (TESS first):

1. **Ingests** light curves of thousands of stars.
2. **Searches** for periodic transit signals (and single events).
3. **Vets** false positives (eclipsing binaries, contamination, systematics).
4. **Crossmatches** against every database of known planets and candidates, including published candidate lists that are not on ExoFOP.
5. **Alerts** only when the candidate is **NEW** and has survived vetting.

### Definition of success (12 months)

| Metric | Target | Why this form |
|---|---|---|
| Latency: MAST release to alert | < 48 h | — |
| Recall on detectable TOIs (expected SNR ≥ 7.1, ≥ 2 transits in the sector) | ≥ 90 %, no regression | Regression guard only: TOIs were found by SPOC/QLP, so this recall is selection-biased |
| Injection-recovery completeness, in bins of period, S/N, number of transits and Tmag | Published per release; at least the Kepler curve (about 76 % at S/N 10, 92 % at 12) | The unbiased measure (Christiansen 2015; Kunimoto 2022 P_det) |
| Empirical false-alarm rate per sector (search run on inverted and scrambled light curves) | Measured; sets the SDE/SNR floors | White-noise FAPs are optimistic (Pont 2006; Thompson 2018) |
| P0 alerts for already-cataloged objects | 0 | Critical-bug invariant |
| Precision of P0 alerts after human review | ≥ 50 % | — |
| Candidates published (RNAAS or paper) and uploaded as CTOIs | ≥ 1 | ExoFOP has required publication first since 2026-08-19 |

## 2. The reality of the field: where new planets still hide

**Context.**
- TESS is in its 3rd extended mission (Sep/2025–Sep/2028), with a budget about 30 % smaller from Oct/2025.
- Sectors are around 101–107 in 2026. Coverage exceeds 98 % of the sky, with 3–4 visits over much of it.
- SPOC, QLP and its Faint-star Search, Planet Hunters TESS, DIAmante, DTARPS, ExoMiner++ and transformer searches have already mined the obvious.
- Searching for "anything" means rediscovering TOIs. Strategy: **niche**, and measure each niche with injection-recovery before investing heavily.

| Niche | What the literature says | How to attack it |
|---|---|---|
| Faint FFI stars (T 13.5–16) | TESS-SPOC FFI covers field stars only to T ≤ 13.5 (Caldwell 2020); QLP stops at 13.5, and prime-mission QLP signals to 13.5 were already vetted (Kunimoto 2022, 1617 TOIs). Noise is ≳ 1000 ppm per transit at T 13.5, so expect mostly giant planets and giant stars. | TGLC light curves (T ≤ 16, all sectors, Gaia-deblended; Han & Brandt 2023) or our own extraction. CBVs on SAP-like flux, dilution correction, giant-star flag. |
| Monotransits and duotransits (P > 25 d) | Predicted yield is about 3× the TOI catalog for P > 25 d (Rodel 2024). Single transits outnumber multi-transit detections 3:1 beyond 45 d (Cooke 2018). Neither SPOC nor QLP searches them on purpose (Guerrero 2021). Competitors: PHT (73 single), Salinas 2025 (88 single), Hawthorn 2024 (85 duo). | Single-event detector (monofind baseline), period posterior from ρ\* (Osborn 2016), duotransit alias lists P = ΔT/n (Cooke 2021), archival ground photometry. Deep single events are often EBs (Gill 2020). |
| M dwarfs | Short transits and strong variability. Detrending hurts on fast rotators; a joint GP plus transit search won in 93 % of cases (Garcia 2024). | Adaptive detrending now; evaluate `nuance` for stars above the red-noise limit. |
| Extra planets in known systems | 17 extra small planets found in already-known K2 systems (Heller 2019). Multi-planet candidates are much more often planets (Lissauer 2012). | Mask known transits and re-search with an S/N-driven cap. `host_known` already exists; add the multiplicity boost. |
| Shallow multi-sector signals | Needs 10+ sectors (continuous viewing zones). | Multi-sector pipeline; P_max from the longest continuous stretch (QLP rule). |
| Kepler/K2 reanalysis with ML | ExoMiner validated 301 Kepler planets (Valizadegan 2022). | Phase 5. |

Evidence from community work: 168 TOIs (through 2021) started as CTOIs. All of them were SPOC/QLP signals that had been triaged out by mistake (Guerrero 2021; Zenodo 5130660). So the community's past yield came from *re-vetting* pipeline signals, not from new detections, and better vetting is itself a niche.

## 3. Architecture

```
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │ 1. INGEST    │──▶│ 2. PREPROC   │──▶│ 3. SEARCH    │──▶│ 4. VETTING   │
 │ MAST/TESScut │   │ QC mask,     │   │ TLS/BLS,     │   │ basic (batch)│
 │ HLSP, TGLC,  │   │ detrend,     │   │ monotransit, │   │ deep (per    │
 │ TIC, Gaia    │   │ CBV (SAP),   │   │ multi-sector │   │ candidate),  │
 └──────────────┘   │ outliers     │   └──────────────┘   │ p_planet     │
        │           └──────────────┘                      └──────┬───────┘
        ▼                                                         ▼
 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │ 0. MIRRORS   │──▶│ 5. CROSSMATCH│◀──│ candidates   │   │ 7. REVIEW    │
 │ Archive, TOI,│   │ ID, cone+PM, │──▶│ NEW / KNOWN_*│──▶│ human queue, │
 │ CTOI, EB cats│   │ period+alias,│   │ severity     │   │ ML feedback, │
 │ published    │   │ transits,    │   └──────┬───────┘   │ paper → CTOI │
 │ candidates   │   │ ephem. match │          ▼           └──────────────┘
 └──────────────┘   └──────────────┘   ┌──────────────┐
                                       │ 6. ALERT     │
                                       │ P0/P1/P2,    │
                                       │ dossier, bot │
                                       └──────────────┘
```

Each stage is a pure Python module with an input/output contract (Parquet/DuckDB), testable in isolation. Orchestration only wires the modules together.

## 4. Data sources

### 4.1 Detection (photometry)

| Source | Access | Coverage | Use |
|---|---|---|---|
| TESS SPOC 2-min / 20-s | `lightkurve`, `astroquery.mast` | ~20k targets/sector | Baseline, benchmark (in use) |
| TESS-SPOC FFI (HLSP) | MAST HLSP | Up to 160k/sector; field stars T ≤ 13.5 | FFI baseline |
| QLP (HLSP) | MAST HLSP | T ≤ 13.5 | Comparison |
| TGLC (HLSP) | MAST HLSP | T ≤ 16, all sectors, PSF with Gaia priors | Faint niche |
| Raw FFI (TESScut) | `lightkurve.search_tesscut`, `eleanor` | Any star | Targets outside the HLSPs |
| Kepler / K2 | `lightkurve` | Legacy | Phase 5 |
| Gaia DR3 (DR4 planned 2 Dec 2026, with epoch photometry) | VizieR, `astroquery.gaia` | — | Neighbors, RUWE, EBs, variables |
| TIC v8.2 | `astroquery.mast.Catalogs` | — | R\*, M\*, Teff, Tmag, contamination; respect phantom/duplicate flags |
| TESS Data Release Notes | MAST | Per sector | Momentum dumps, scattered light, anomalies |

FFI cadence changed over the mission: 30 min (Years 1–2), 10 min (Years 3–4), 200 s (Year 5 on). Transit-shape tests and triceratops must be given the real exposure time.

### 4.2 Cross-check ("does it already exist?")

| Database | Access | Answers | Refresh |
|---|---|---|---|
| NASA Exoplanet Archive `pscomppars` / `ps` | TAP | Confirmed planet? | Daily |
| ExoFOP-TESS TOI + CTOI | CSV `download_toi.php` / `download_ctoi.php` | Candidate already submitted? **Source of truth for freshness**: the Archive `toi` table syncs from it only about weekly | Daily |
| NASA Exoplanet Archive `toi` | TAP | TFOPWG disposition (APC/CP/FA/FP/KP/PC) | Daily |
| exoplanet.eu | CSV export | European catalog (loose inclusion; map statuses carefully) | Weekly |
| TESS EB catalogs: Prša 2022 (2-min, S1–26) and TESS Ten Thousand (Kostov 2025, FFI, S1–82) | VizieR / MAST | Known eclipsing binary? | Monthly |
| Gaia DR3 EB catalog (Mowlavi 2023; 25–50 % complete) | VizieR | EB at or near the target? Absence is weak evidence | Per candidate |
| Published candidate lists not necessarily on ExoFOP: ExoMiner++, Planet Hunters TESS, DIAmante, DTARPS, Salinas 2025, Hawthorn 2024, LEO-Vetter | Journal / VizieR / MAST tables | Already published by someone? | Monthly |
| SIMBAD / VizieR | `astroquery` | Cross-identifiers, object type | Per candidate |
| ADS API + arXiv astro-ph.EP | REST | Published but not yet in any catalog? | Per candidate |

Network rule: the batch path (preprocess → search → basic vetting → crossmatch) **never** uses the network; it reads only Parquet and local mirrors. Network only in (a) ingestion and mirror sync, with caching, and (b) per-candidate deep vetting, with caching and failure tolerance: without network the candidate stays pending, never approved.

## 5. The "does it already exist?" engine (crossmatch)

Two separate questions: **which star?** and **which signal?**

### Star (host)

1. **Exact ID.** TIC (implemented). Gaia DR3, KIC/EPIC and HD/HIP are planned; map Gaia DR2 to DR3 with `dr2_neighbourhood`, never assuming the ID carried over.
2. **Position.** A 21″ cone (1 TESS pixel) for the host, and 120″ for neighbors. For catalogs that give only a position (exoplanet.eu, published lists), the star's proper-motion track from J2000 to the observation epoch is used.

### Signal (for each known object of the host or neighbor)

3. **Period and aliases.**
   - P_cand/P_known in {1, 2, 1/2, 3, 1/3, 3/2, 2/3}.
   - Tolerance = max(1 %, 3σ_rel of the candidate), capped at 3 %. Beyond 1 % the phase must agree.
   - A missing catalog σP is taken as 10⁻⁴·P instead of zero drift.
   - When the phase tolerance reaches 0.5, `phase_checked = False` records that the check carried no information.
4. **Transit by transit.** At least 50 % of the candidate's transits must fall within max(0.5·T14, 1 h) + 3σ of the propagated ephemeris, **and** the binomial chance probability must be < 1 %.
   - Ephemerides with 3σ > min(0.25 d, 0.1·P) are skipped.
   - Phase 0.5 is never tested for a confirmed planet.
   - Every matching object is collected before precedence is applied.
   - Near-misses (chance between 1 % and 10 %) stay `NEW` with the token `partial_known_transit_coincidence`, which caps them at P2.
   - The old rule matched by chance 36 % of the time; this one does 0.3 %.
5. **Integer harmonics on the host:** n or 1/n up to 50 (Thompson 2018), with a phase check and chance probability < 5 %.
6. **Known objects without a period:** a match if the candidate's ephemeris predicts their epoch. Otherwise the signal is flagged `periodless_known_on_host` and capped at P2.

**Rules.**
- Only a match on both star **and** signal makes the object known.
- A known host with a period incompatible with all its objects is `NEW` with `host_known = True` (additional-planet niche; never discard).
- Alias 1 matches even with poor phase.
- For planets, alias ≠ 1 requires a consistent phase. Otherwise planets near 2:1, 3:2 and 3:1 resonance (1–2 % off the exact ratio) would be swallowed.
- For eclipsing binaries there is no resonance exemption. An EB catalog row or an FP/EB disposition matched at any alias is `KNOWN_FP`.
- `host_eb` ignores EB rows that are the host's own planet.
- Precedence: planet > FP > TOI > CTOI > published candidate > EB catalog.

### Run-level checks (`crossmatch/runlevel.py`, offline)

7. **Epoch spikes.**
   - Common-epoch systematics: a 0.25 d bin in which far more unrelated targets have a transit than chance allows.
   - `epoch_spike_frac` ≥ 0.5 means no alert.
   - Sector 107: 4 spike bins, 437 NEW flagged. Held-out check: 42 signals with every transit in a spike, against 0.5 expected by chance.
8. **Shared signals.** The same period (alias 1, 2 or 1/2) and T0 on another target within 120″.
   - The star whose required intrinsic depth is plausible and whose eclipsed flux (depth × flux) is larger is the `source`.
   - The other star is the `victim`.
   - Within 2″ the pair is a `duplicate` (TIC split entries; Paegert 2021).
   - Victims and duplicates get no alert; sources are capped at P2.
   - Kepler-style ephemeris matching with ratios up to 50 carries no information inside a single TESS sector (3720 vs 3630 under scrambled epochs), so proximity is required.
9. **Duotransits (planned).** A duotransit is crossmatched as its whole alias list P = ΔT/n, pruned by coverage and ρ\* (Cooke 2021).

### Output classes

| Class | Meaning | Action |
|---|---|---|
| `KNOWN_PLANET` | Confirmed (Archive, exoplanet.eu, KOI/K2 confirmed) | Log, no alert (recall test) |
| `KNOWN_TOI` / `KNOWN_CTOI` | Already a candidate on ExoFOP | Log; if our detection improves the period → P2 |
| `KNOWN_PUBLISHED` | In a published candidate list (DIAmante, DTARPS, LEO-Vetter, ExoMiner++, KOI/K2 candidates, exoplanet.eu non-confirmed) | Log, no alert |
| `KNOWN_FP` | FP/FA disposition, or a cataloged EB (Prša 2022, TESS Ten Thousand, Gaia DR3 EB) | Discard; feeds ML training |
| `NEARBY_KNOWN` | Known object nearby with a compatible period | Probable contamination; discard unless the centroid is on target |
| `NEW` | No match (with flags `host_known`, `host_eb`, `epoch_spike_frac`, `shared_signal_role`) | Vetting, then severity |
| `UNVERIFIED` | Would be `NEW`, but a mirror is missing or stale for its policy | Alerting forbidden; sync and reclassify |

**Mirror freshness, by source:**
- ExoFOP TOI/CTOI and the Archive: 48 h.
- exoplanet.eu and K2: 7 d.
- KOI: 30 d.
- Static VizieR catalogs: by version.

Every sync writes a manifest (rows, sha256, version). Right before sending, the alert gate re-classifies every P0/P1 against freshly loaded mirrors.

## 6. Automatic vetting (gate before the alert)

### 6.1 Basic tests (batch, offline)

| # | Test | Limit in use (`config/thresholds.yaml`) | Literature | Failure indicates |
|---|---|---|---|---|
| 1 | TLS SDE | ≥ 9 (veto) | SDE 7 ≈ 1 % FAP (Hippke & Heller 2019); 9.1 ≈ 10⁻⁴ (TLS docs), white noise only | Noise |
| 2 | Transit SNR | ≥ 7.1 (veto), recomputed with the physical T14 | SPOC MES threshold | Noise |
| 2b | S/N_pink | ≥ 9 (QLP), on the T14 scale; soft fail, because as a veto it removed 10 % of the known planets that pass | Pont 2006; Guerrero 2021; Kunimoto 2023 | Red noise |
| 3 | Number of transits | ≥ 2 epochs with ≥ 50 % coverage (veto); 1 → monotransit flow | SPOC ≥ 2 | — |
| — | Independence | ≥ 50 % of in-transit points survive masking stronger signals (veto) | — | Duplicate of a stronger signal |
| — | Period halving | A phase-0.5 "secondary" equal to the primary (within 3σ, same duration) triggers re-vetting at P/2 | Thompson 2018 | Detection at 2P |
| 4 | Odd-even | fail 3σ, veto 5σ | LEO: 3σ | EB at 2P |
| 5 | Secondary at phase 0.5, plus a scan at any phase | fail 3σ; veto 5σ only if ≥ 10 % of the primary; scan 5σ (hard fail) | LEO albedo check (planned) | EB |
| 6 | Shape | τ/T14 ≤ 0.35 and Rp/R\* ≤ 0.3 (hard fail); KDR25 k + b < 1.04 from a limb-darkened fit | Thompson 2018 | Grazing EB |
| 7 | Derived radius | fail > 22.4 R⊕. Veto > 33.6 R⊕ only with a reliable R\* (log g ≥ 3.5) **and** another EB sign | Mullally 2015 | EB / brown dwarf |
| 8 | Duration vs stellar density | 0.15 ≤ T_obs/T_pred(b = 0) ≤ 1.67; fits on a bound give no result | Kipping 2010; LEO | Blend, wrong star |
| 9 | Centroid (MOM_CENTR) | Significance from 200 fake out-of-transit epochs; δ_ap = CROWDSAP·δ; no result for Tmag < 7 or < 3 transits | Bryson 2013; Kostov 2019 | Contaminating neighbor |
| 11 | Momentum dumps and segment edges | ≤ 50 % of transits near a dump or edge | LEO | Systematic |
| 12 | Transit consistency | p-value ≥ 0.001 | Coughlin 2016 | Systematic, one dominant event |

**Light curve used for vetting.** Each sector is re-detrended with its own window (never below 3×T14), with the transits masked at phase 0 and 0.5 (Hippke 2019). On unbinned 2-min data, a 12 h transit keeps 99 % of its depth this way, against 50 % without the mask.

### 6.2 Deep tests (per candidate, network, resumable)

| # | Test | What it does |
|---|---|---|
| 9 | `tpf_difference_image` | Difference-image centroid against the **catalog** position, propagated with proper motion (> 3σ and > 1 px fails; < 3 transits gives no result) |
| 10 | `gaia_neighbors` | Can each Gaia DR3 neighbor produce the depth? Required depth = δ·F_target,ap/F_neighbor,ap, with a Gaussian PSF over the real aperture. Fails if a feasible neighbor sits at the difference centroid |
| — | `gaia_eb` | Gaia DR3 EB catalog within 21″ |
| — | `simbad_type` | Fails only on EB\*, SB\* and El\*; other types are informational |
| 12b | `other_sectors` | Presence in other sectors: BLS against a noise floor measured with the candidate's transits masked, plus a blind search |
| 13 | `fpp_triceratops` | FPP and NFPP: 3 repeats, measured flux scatter, real exposure time; degenerate runs are rejected. FPP ≥ 0.5 or NFPP > 0.1 fails |

### 6.3 Output

**Verdict.**
- FAIL on any veto.
- FAIL on any hard fail: `tpf_difference_image`, `fpp_triceratops`, `secondary_scan`, `shape`.
- FAIL on more than one soft fail.
- Otherwise PASS. The multiplicative score is kept only for ranking.

**`p_planet` (schema 2).**
- A logistic model, unweighted, with a two-sided duration feature and the secondary feature clipped at ≥ 0.
- Missing-value flags are merged.
- C is chosen by nested CV grouped by TIC, with Platt scaling.
- Negatives can include signals from inverted and scrambled null runs.
- It is stored as `p_rank`, together with the prior-corrected `p_abs` (display only, `severity.new_prior` = 0.05 is an assumption) and the `model_version`.

## 7. Severity, alerts and dossier

Rules in use (`alerts/severity.py`). `p` is `p_rank` after deep-test penalties (applied in odds space). `p1_cut` and `p2_cut` are the model's operating points: 90 % out-of-fold recall on known planets for P2, and FPR ≤ 1 % (but at least 70 % recall) for P1.

| Severity | Condition | Channel | Latency |
|---|---|---|---|
| none | not `NEW`; any veto; `epoch_spike_frac` ≥ 0.5; shared-signal `victim` or `duplicate`; basic FAIL with `p` < `p2_cut` | — | — |
| P0 | `NEW`, basic pass, score ≥ 0.8 **and** `p` ≥ `p1_cut`. Deep vetting complete (TPF and Gaia neighbors passed, FPP ok). FPP < 0.1, NFPP < 10⁻³, Rp < 8 R⊕, SNR ≥ 15, 2-min cadence (Giacalone 2021 validation region) | Immediate Telegram/Discord + e-mail | Minutes |
| P1 | Same as P0, but deep vetting incomplete or outside the validation region | Immediate | Minutes |
| P2 | Basic pass below the P1 cuts; basic FAIL rescued by `p` ≥ `p2_cut`; host is an EB; star without radius; NFPP > 0.1; shared-signal `source`; `periodless_known_on_host`; `partial_known_transit_coincidence` | Review queue (`planethunter candidates`); weekly digest planned | — |

**Principles.**
- The ML never decides alone, in either direction: it only lowers priority.
- FPP < 0.1 is a project choice for alerting, between the "likely planet" (< 0.5) and "validated" (< 0.015) levels.
- No candidate is described as validated without high-resolution imaging. Without it, 72 % of imaging-dependent validations fail (Collier 2026, preprint).

**Send-time gate**, re-evaluated before sending:
- class `NEW` after a fresh re-classification;
- every mirror fresh for its policy;
- no identical alert in the last 30 days.

**Dossier and review.**
- The per-candidate dossier (HTML) contains: the raw and detrended curve, the phase fold, odd-even, the secondary window and a per-transit view; the TPF and difference image with the TIC position and Gaia sources; the parameter table; crossmatch results with links (ExoFOP, Archive, SIMBAD); FPP/NFPP; and the recommended next action.
- In the human review queue (`planethunter review`), a candidate is approved, rejected with a reason, or marked "needs follow-up". Each decision becomes an ML label.

## 8. Technical stack

| Layer | Choice | Reason / status |
|---|---|---|
| Language | Python 3.12, `uv`, `ruff`, `pytest` | Astro ecosystem |
| Astro | `lightkurve`, `astroquery`, `astropy`, `wotan`, `transitleastsquares` 2.0, `triceratops` (isolated env), `batman` | Community standard |
| FFI photometry | TGLC HLSP first; `eleanor`/TESScut for stars outside it | TGLC is Gaia-deblended to T = 16 |
| Data | Parquet (float32) + DuckDB | Zero infra at the start |
| Relational database | DuckDB → PostgreSQL + `q3c` when there is a multi-user dashboard | Scale on demand |
| Parallelism | `ProcessPoolExecutor`, one TLS thread per target | Measured: 0.7 s vs 18.7 s per target with 8 threads on Windows |
| GPU | Experimental `gpu_bls.py` (PyTorch), not wired in | Measured: a GPU pre-filter loses recall or saves only about 6 %. Evaluate GERBLS (CPU, O(n log n)) for injection campaigns instead |
| ML | Logistic `p_planet` now; Phase 5 CNN (global + local view) with Astronet-Triage-v2 / ExoMiner++ as baselines | — |
| Orchestration | `typer` CLI + OS scheduler → Prefect 3 | Simple first |
| Alerts | Telegram Bot API, Discord webhook, SMTP | Low cost |
| Infra | Local (Windows) → Docker Compose → optional cloud VM | Controlled cost |

## 9. Data model (as implemented, `src/planethunter/db/schema.sql`)

Main columns; units in the column names.

- `targets`: tic_id, ra_deg, dec_deg, pmra_mas_yr, pmdec_mas_yr, tmag, teff_k, logg_cgs, radius_rsun, mass_msun, crowdsap
- `lightcurves`: tic_id, sector, author, camera, ccd, procver, data_release, source_file, sha256, n_points, path
- `search_runs`: run_id, mode, sector, author, pipeline_version, params_hash, params_json, counts, started_at, finished_at
- `search_done`: run_id, tic_id, status, n_signals, elapsed_s, error (makes runs resumable)
- `signals`: signal_id, run_id, tic_id, sectors, author, iteration, period_days, t0_btjd, duration_hours, depth_ppm, sde, snr, n_transits, odd_even_mismatch_sigma, rp_rs, fap, edge_transit_fraction, detrend_window_days, alias_factor, transit_times_json, pipeline_version, params_hash
- `crossmatch`: signal_id, match_class, host_known, host_eb, matched_name, matched_source, alias, phase_consistent, separation_arcsec, match_type, n_host_objects, n_nearby_objects, mirror_ages_json
- `vetting`: signal_id, level (basic/deep), score, verdict, vetoed_by, failed, deep_pending, trapezoid fit, fpp, nfpp, p_planet, tests_json, params_hash
- `candidates`: signal_id, tic_id, run_id, match_class, verdict, score, severity, review_status, review_note, dossier_path
- `alerts`: signal_id, channel, severity, status (sent/pending/failed/dry_run), message, error

Mirror freshness lives in each mirror's Parquet (`synced_at`), not in a table. Planned: a `gaia_id` and contamination ratio on `targets` (for dilution and Gaia flags), and a `published_candidates` mirror (§17 #5).

## 10. Roadmap

| Phase | Status | Deliverables | Acceptance criterion |
|---|---|---|---|
| **0. Foundation** | done | Repo, `uv`, CLAUDE.md, agents, skills, benchmark dataset | `pytest` green |
| **1. Baseline search** | done | SPOC 2-min ingestion, wotan in two variants, parallel iterative TLS, alias refinement | Recall 91.1 % on detectable TOIs (sector 69), 1.3 min for 173 targets |
| **2. Crossmatch** | core done | 5 mirrors, ID + cone + aliases with phase + transit by transit, classes | 100 % of known planets `KNOWN_*`. Missing: proper motion, ephemeris matching, published-candidate mirrors |
| **3. Vetting + alert** | done (v1.0.0) | 13 basic tests, deep vetting, triceratops, `p_planet`, severity, HTML dossier, Telegram/Discord dry-run, review CLI | Zero P0 on `KNOWN_*`; first full sectors run (69 partial, 107 complete) |
| **3.5 Literature alignment** | next | Tier 1 of §17 | Before/after benchmark attached; false-alarm rate measured |
| **4. Niche and scale** | not started | TGLC faint stars, monotransit detector, duotransit alias lists, multi-sector, injection-recovery completeness, Prefect | Processes a new sector < 48 h after release; completeness map published |
| **5. ML + literature** | not started | CNN on TOIs/FPs + injections (not injections alone: Osborn 2020); active learning; ADS/arXiv scout; publication → CTOI flow | ML cuts candidates to review ≥ 5× at equal recall; 1st candidate published |

## 11. Agent team (Claude Code, in `.claude/agents/`)

| Agent | Role | When to invoke |
|---|---|---|
| `astro-domain-expert` | Scientific consultant: transit physics, false-positive taxonomy, realistic limits | Thresholds, strange signals, dossier review |
| `data-ingestion-engineer` | MAST, lightkurve, TESScut, HLSPs, Parquet, cache | Downloading/storing light curves |
| `transit-search-engineer` | Detrending, TLS/BLS, monotransit, performance | The search stage |
| `vetting-scientist` | Vetting tests, centroid, triceratops, score | The vetting stage |
| `crossmatch-engineer` | Mirrors, TAP/CSV, aliases, classes | "Does it already exist?" |
| `ml-engineer` | Labeled dataset, calibration, CNN, active learning | `p_planet`, Phase 5 |
| `platform-engineer` | Data model, DuckDB/Postgres, Prefect, Docker, CLI | Infra and orchestration |
| `alerting-engineer` | Dossier, bots, digests, review queue | Notification and UI |
| `research-scout` | arXiv/ADS for methods and already-published candidates; keeps [LITERATURE.md](LITERATURE.md) current | Monthly, and per P0 |
| `qa-benchmark-engineer` | Injection-recovery, recall benchmark, false-alarm rate, regression tests | Before every merge into search/vetting/crossmatch |

Typical flow: main session orchestrates → `astro-domain-expert` validates → area engineer implements → `qa-benchmark-engineer` measures → `/code-review`.

## 12. Skills (in `.claude/skills/`)

| Skill | Content |
|---|---|
| `tess-data-access` | lightkurve/astroquery/TESScut recipes, Parquet cache, MAST limits |
| `transit-search` | TLS/BLS parameters, period grids, wotan detrending, SDE/SNR thresholds |
| `candidate-vetting` | The vetting tests with formulas and code |
| `exoplanet-crossmatch` | TAP queries, ExoFOP CSV, cone search with PM, aliases, classes |
| `injection-recovery` | Injecting synthetic transits, measuring completeness and false-alarm rate |
| `alert-dossier` | Dossier structure, severities, Telegram/Discord integration |

## 13. Operational KPIs

- Recall on detectable TOIs per sector (regression guard, ≥ 90 %).
- Injection-recovery completeness by period, S/N, number of transits and Tmag, compared with Kunimoto 2022 P_det.
- Empirical false-alarm rate per sector (inverted and scrambled light curves).
- Vetting pass rates per class: confirmed planets (target ≥ 80 %) and TFOPWG false positives (target ≤ 10 %).
- `p_planet` reliability (calibration curve) on reviewed NEW candidates.
- P0 precision after review (≥ 50 %); `NEW` per sector before and after ML (≥ 5× reduction).
- Processing time per sector; release-to-alert latency.
- False P0 on `KNOWN_*` (0; any occurrence is a critical bug).
- Mirror sync (failure > 48 h = internal alert).

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Rediscovering only known things | Niche strategy (§2); crossmatch against catalogs **and** published candidate lists before alerting |
| Recall that looks good on TOIs but not on new signals | Injection-recovery as a co-primary KPI (§1) |
| Contamination by neighbors (21″ pixels) | Centroid, difference image, Gaia in the aperture, cross-target ephemeris matching, triceratops NFPP |
| Systematics that mimic transits | Edge and dump tests, ephemeris matching across stars, empirical false-alarm rate, other sectors |
| Over-trusting FPP | Use triceratops only in its valid region; never claim validation without follow-up and imaging |
| Noisy training labels | TFOPWG labels are noisy (ExoMiner++); grouped CV, prior correction, human review as labels |
| ExoFOP publication gate (since 2026-08-19) | Publish first (RNAAS citing a published method, or a paper), or partner with a TFOP group |
| Data volume | Parquet float32, process and discard FITS, per sector |
| MAST/ExoFOP/ADS rate limits | Local mirrors, backoff, cache, never an API in the critical path |
| Over-claiming | Fixed vocabulary: "candidate", never "discovery" |
| API drift (TAP, columns) | Contract tests on the mirrors |
| Dependence on local hardware | Per-sector, resumable pipeline; Docker to move to the cloud |

## 15. Ethics and community

**Submitting a candidate.**
- Since 2026-08-19 ExoFOP accepts community candidates only **after publication in a peer-reviewed journal**, with upload approval. The route is: dossier, then RNAAS or paper, then CTOI upload request.
- Promotion to TOI is a decision of the TESS TOI Team.
- A signal at an integer multiple of a known period is attached to the existing object, not submitted as a new one.

**Citations.** In any publication, cite the pipelines and data: TESS (Ricker 2015), SPOC (Jenkins 2016), QLP, TESS-SPOC, TGLC if used, Gaia DR3, the TIC, the NASA Exoplanet Archive and ExoFOP (Christiansen 2025), and every catalog and tool listed in [LITERATURE.md](LITERATURE.md).

**Conduct.**
- Never publicly announce a "discovery" before validation and independent follow-up.
- Keep data and code open: it encourages collaboration and follow-up.

## 16. Immediate next steps

1. Finish sector 107 (deep vetting, severity, review) and record its validation in `docs/benchmarks/`.
2. Run Tier 1 of §17 in order, with a before/after benchmark for each change.
3. Start Phase 4 with injection-recovery: the completeness map decides which niche gets the effort.

## 17. Backlog from the literature review (2026-10-09)

Ranked by impact per cost. "Adopt" means the literature is clear. "Evaluate" means measure with the benchmark before deciding. Every change to search or vetting reruns the benchmark (CLAUDE.md).

**Status (2026-10-13).** A code audit against this literature (2026-10-10) found implementation bugs beyond this list. They were fixed together with the items below; §5–§7 describe the result.

**Done:**
- **Tier 1:** #1 (NFPP, validation region, exptime, measured scatter, repeats), #2 (two-sided duration, clipped secondary, unweighted fit, operating points, `p_abs`, provenance), #3 (as run-level epoch spikes and shared signals: Kepler-style ratio matching carries no information inside one TESS sector), #4 (S/N_pink stored and tested as a soft fail; null runs `--null inverted|scrambled` measure the false-alarm rate), #5 (TESS Ten Thousand, ExoMiner++, DIAmante, DTARPS, LEO-Vetter, Kepler KOI, K2; class `KNOWN_PUBLISHED`), #6 (vetting fits run on unbinned flux, plus a limb-darkened batman fit with KDR25).
- **Tier 2:** #9 (window ≥ 3×T14 with masked re-detrend, QLP period rule, duration ceiling 1.67, SNR recomputed after alias refinement) and most of #10 (catalog-position reference with proper motion, indeterminate below 3 transits, empirical centroid significance).
- **Audit fixes:**
  - TLS duration fill-factor bias.
  - Period halving.
  - `other_sectors` noise floor.
  - Neighbor dilution formula.
  - Transit-by-transit chance test.
  - EB alias rules.
  - Send-time re-crossmatch.
  - The ML can only lower priority.

**Open:**
- **Tier 1:** Planet Hunters TESS and Hawthorn 2024 mirrors (not on VizieR).
- **Tier 2:**
  - #7 (LEO-Vetter model-shift/SWEET/albedo, ghost);
  - #8 (injection-recovery completeness);
  - PRF fit and RUWE in #10;
  - #11 (TGLC);
  - #12 (monotransit/duotransit flow).
- **Tier 3:** all.

### Tier 1 — adopt, low cost

| # | Change | Basis | Cost |
|---|---|---|---|
| 1 | FPP gate with NFPP: P0 needs NFPP < 10⁻³; NFPP > 0.1 fails; cap at P1 outside Rp < 8 R⊕, SNR ≥ 15, 2-min data. Pass `exptime` per cadence and `dilution_corrected=False` for non-PDCSAP flux. Run triceratops 3–5 times and report the scatter. | Giacalone 2021 | Hours + FPP CPU |
| 2 | `p_planet` model: drop `class_weight="balanced"` or correct the intercept; make the duration feature two-sided (\|log ratio\|): the linear model has a +0.30 coefficient on log duration ratio, so too-long durations *raise* p (sector 107: 115 of 119 rescued signals failed duration); validate on sectors not used in training; reliability diagram per fold; out-of-distribution flag. | Niculescu-Mizil & Caruana 2005; Armstrong 2021; sector 107 | Hours |
| 3 | Cross-target ephemeris matching inside each run and against the EB catalogs; magnitude-dependent nearby radius. | Coughlin 2014; Thompson 2018 | 1–2 days |
| 4 | S/N_pink (σ_r on the T14 scale) as a hard gate around 9, keeping white SNR ≥ 7.1 as a soft gate. Measure the false-alarm rate on inverted and scrambled light curves and set the SDE/SNR floors from it. | Pont 2006; Guerrero 2021; Kunimoto 2023; Thompson 2018 | 1 day + 2× CPU for one sector |
| 5 | New mirrors: TESS Ten Thousand EBs, ExoMiner++, Planet Hunters TESS, DIAmante, DTARPS, Salinas 2025, Hawthorn 2024, LEO-Vetter; class `KNOWN_PUBLISHED`; ExoFOP CSV as the freshness source. | Section 9–10 of LITERATURE.md | 1–2 days |
| 6 | Shape and density tests on unbinned data. | Kipping 2010b | Hours |

### Tier 2 — evaluate, medium cost

| # | Change | Basis |
|---|---|---|
| 7 | Port LEO-Vetter flux tests: model-shift MS1–3, SWEET, chases, mean-to-median, asymmetry, model vs line, albedo check. Add the ghost/halo diagnostic. | Coughlin 2016; Thompson 2018; Kunimoto 2025 |
| 8 | Injection-recovery completeness KPI (flux-level, Mandel-Agol, binned by period, S/N, number of transits and Tmag). | Christiansen 2013–2020; Burke 2015; Kunimoto 2022 |
| 9 | Search geometry. Window ≥ 3× T14 per duration bin (or adaptive). Period range by the QLP rule (a ≥ 2 R\* to the longest continuous stretch). Duration ceiling raised to about 1.7–2×. Iterative cap driven by S/N instead of 3. | Hippke 2019; Kunimoto 2023; Kipping 2010; Li 2019 |
| 10 | Centroid. PRF fit on the difference image. Catalog-position reference in crowded fields. "Indeterminate" with fewer than 3 transits. Add RUWE and `ipd_frac_multi_peak` flags. | Bryson 2013; Kostov 2019; Belokurov 2020; Fabricius 2021 |
| 11 | Faint niche via TGLC, with CBV/dilution handling and a giant-star flag. | Han & Brandt 2023; Kunimoto 2022 |
| 12 | Monotransit and duotransit flow. monofind baseline. Period posterior from ρ\*. Alias lists P = ΔT/n crossmatched in full. Archival ground photometry. | Hawthorn 2024; Osborn 2016; Cooke 2021; Gill 2020 |

### Tier 3 — later

| # | Change | Basis |
|---|---|---|
| 13 | Joint GP + transit search (`nuance`) for active M dwarfs. | Garcia 2024 |
| 14 | GERBLS for large injection campaigns. | Ment 2026 |
| 15 | Multiplicity boost for `host_known` candidates. | Lissauer 2012; Valizadegan 2023 |
| 16 | Phase 5 CNN against the Astronet-Triage-v2 and ExoMiner++ baselines. | Tey 2023; Valizadegan 2025 |
| 17 | Positional probability (Transit-APP) as an FPP prior; DEATHSTAR for locating eclipsing neighbors. | Bryson & Kunimoto 2025; Ross 2024 |

## Verification references

- HEASARC TESS sectors: https://heasarc.gsfc.nasa.gov/docs/tess/sector.html
- NASA Exoplanet Archive TAP: https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html
- TOI columns: https://exoplanetarchive.ipac.caltech.edu/docs/API_toi_columns.html
- ExoFOP-TESS and its news (candidate policy): https://exofop.ipac.caltech.edu/tess/news.php
- CTOI assessment: https://zenodo.org/record/5130660
- TFOP: https://heasarc.gsfc.nasa.gov/docs/tess/tfop.html
- Gaia DR4 date: https://www.cosmos.esa.int/web/gaia/news-2026
- PLATO (launch planned early 2027): https://www.esa.int/ESA_Multimedia/Videos/2026/03/Plato_s_launch_on_Ariane_6
- Full literature list: [LITERATURE.md](LITERATURE.md)
