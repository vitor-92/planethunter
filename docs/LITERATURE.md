# Literature basis

The papers, catalogs and documents that PlanetHunter's design rests on, and what each one means for this project. [PLAN.md](PLAN.md) cites this list; §17 of the plan turns the gaps found here into a prioritized backlog.

Compiled 2026-10-09.

**How the list was verified.**
- **Existence:** every entry was checked against its DOI or arXiv record. Nothing here comes from memory alone.
- **Citations:** the OpenAlex or Crossref count on 2026-10-09. ADS counts usually run 10–30 % higher. The counts show which works are standard, not which are correct.
- **Numbers:** the ones quoted under "Take" were read from the paper's full text unless marked *(abstract)*.
- **Preprints:** listed separately at the end, because they are not refereed and are only indicative.
- **ADS:** every entry can be found with the query `doi:"<DOI>"`.

---

## 1. Transit physics and noise

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Mandel & Agol 2002, ApJ 580, L171 — analytic limb-darkened transit light curves | [10.1086/345520](https://doi.org/10.1086/345520) | 2294 | The model behind the TLS template and `batman`. Injection-recovery must inject Mandel-Agol transits, never boxes. |
| Seager & Mallén-Ornelas 2003, ApJ 585, 1038 — unique solution of planet and star parameters from a transit | [10.1086/346105](https://doi.org/10.1086/346105) | 888 | Shape plus period gives the stellar density ρ\*. This is the basis of the duration-vs-density test. |
| Kipping 2010a, MNRAS 407, 301 — approximate expressions for the transit duration | [10.1111/j.1365-2966.2010.16894.x](https://doi.org/10.1111/j.1365-2966.2010.16894.x) | 118 | Eccentricity scales T14 by √(1−e²)/(1+e sin ω), up to about 1.7× at e = 0.5. A duration ceiling of 1.3× the circular value penalizes eccentric warm planets. |
| Kipping 2010b, MNRAS 408, 1758 — "Binning is sinning" | [10.1111/j.1365-2966.2010.17242.x](https://doi.org/10.1111/j.1365-2966.2010.17242.x) | 316 | Binning smears ingress and egress and biases ρ\* low. Shape and density fits belong on unbinned data, not on the 10-min search series. |
| Winn 2010, "Transits and Occultations", in *Exoplanets* (Univ. Arizona Press) | [arXiv:1001.2010](https://arxiv.org/abs/1001.2010) | 89 | Standard formulas for T14, T23, b, a/R\* and depth. Reference for the V-shape metric. |
| Pont, Zucker & Queloz 2006, MNRAS 373, 231 — red noise and transit detection | [10.1111/j.1365-2966.2006.11012.x](https://doi.org/10.1111/j.1365-2966.2006.11012.x) | 560 | Real thresholds are much higher than white-noise estimates. Use σ² = σ_w²/n + σ_r²/N_tr, with σ_r measured on the transit timescale ("signal-to-pink-noise"). |

## 2. TESS mission, pipelines and data products

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Ricker et al. 2015, JATIS 1, 014003 — TESS | [10.1117/1.JATIS.1.1.014003](https://doi.org/10.1117/1.JATIS.1.1.014003) | 4080 | Mandatory citation. |
| Jenkins et al. 2016, Proc. SPIE 9913, 99133E — the TESS SPOC | [10.1117/12.2233418](https://doi.org/10.1117/12.2233418) | 1054 | Mandatory citation for 2-min products. PDCSAP is already corrected for crowding. |
| Smith et al. 2012, PASP 124, 1000; Stumpe et al. 2012, PASP 124, 985; Stumpe et al. 2014, PASP 126, 100 — Presearch Data Conditioning | [10.1086/667697](https://doi.org/10.1086/667697), [10.1086/667698](https://doi.org/10.1086/667698), [10.1086/674989](https://doi.org/10.1086/674989) | 1033 / 809 / 686 | PDCSAP is already cotrended with CBVs. Do not apply CBVs again to PDCSAP: only to SAP or to our own FFI photometry. |
| Jenkins 2002, ApJ 575, 493 — solar-like variability and detectability | [10.1086/341136](https://doi.org/10.1086/341136) | 367 | Adaptive whitening plus a matched filter (the TPS approach). It is the principled alternative to "detrend, then white-noise SNR". |
| Jenkins, Caldwell & Borucki 2002, ApJ 564, 495 — tests to establish confidence in transit planets | [10.1086/324143](https://doi.org/10.1086/324143) | 197 | The logic behind the 7.1σ threshold: it controls false alarms over the number of stars and trials searched *(abstract)*. |
| Jenkins et al. 2010, Proc. SPIE 7740, 77400D — Kepler TPS | [10.1117/12.856764](https://doi.org/10.1117/12.856764) | 229 | SES/MES on whitened flux. Kepler required ≥ 3 transits; TESS SPOC requires ≥ 2. |
| Twicken et al. 2016, AJ 152, 158 — final Kepler TPS (DR25) | [10.3847/0004-6256/152/6/158](https://doi.org/10.3847/0004-6256/152/6/158) | 83 | TPS searches 14 durations from 1.5 to 15 h. A duration grid out to 15 h is the norm. |
| Twicken et al. 2018, PASP 130, 064502 — Kepler Data Validation I | [10.1088/1538-3873/aab694](https://doi.org/10.1088/1538-3873/aab694) | 322 | DV tests: weak secondary, EB discrimination, difference-image centroid, statistical bootstrap, optical ghost. The same code produces the SPOC TESS DV reports, a free second opinion for 2-min targets. |
| Li et al. 2019, PASP 131, 024506 — Kepler Data Validation II | [10.1088/1538-3873/aaf44d](https://doi.org/10.1088/1538-3873/aaf44d) | 247 | Multi-planet search: fit, remove, search again until nothing is left, with no fixed cap. |
| Guerrero et al. 2021, ApJS 254, 39 — the TOI catalog from the Prime Mission | [10.3847/1538-4365/abefe1](https://doi.org/10.3847/1538-4365/abefe1) | 392 | See the notes after this table. |
| Huang et al. 2020a, b, RNAAS 4, 204 and 206 — QLP photometry of 10 M stars | [10.3847/2515-5172/abca2e](https://doi.org/10.3847/2515-5172/abca2e), [10.3847/2515-5172/abca2d](https://doi.org/10.3847/2515-5172/abca2d) | 278 / 176 | QLP: multi-aperture FFI photometry, T ≤ 13.5. |
| Kunimoto et al. 2021, RNAAS 5, 234 — QLP for the first extended-mission year | [10.3847/2515-5172/ac2ef0](https://doi.org/10.3847/2515-5172/ac2ef0) | 70 | QLP Year 3 light curves. |
| Caldwell et al. 2020, RNAAS 4, 201 — TESS-SPOC FFI target lists | [10.3847/2515-5172/abc9b3](https://doi.org/10.3847/2515-5172/abc9b3) | 169 | See the notes after this table. |
| Doyle et al. 2024, MNRAS 529, 1802 — the TESS-SPOC FFI sample explored with Gaia | [10.1093/mnras/stae616](https://doi.org/10.1093/mnras/stae616) | 6 | About 2.8 M TESS-SPOC FFI stars in sectors 1–55. The sample is not magnitude-limited. Use it as the selection function for completeness. |
| Han & Brandt 2023, AJ 165, 71 — TESS-Gaia Light Curves (TGLC) | [10.3847/1538-3881/acaaa7](https://doi.org/10.3847/1538-3881/acaaa7) | 73 | PSF photometry with Gaia DR3 priors and deblended neighbors, at MAST down to **T = 16** for all sectors. The most direct source for the 13.5–15 niche. |
| Powell et al. 2022, RNAAS 6, 111 — GSFC-ELEANOR-LITE | [10.3847/2515-5172/ac74c4](https://doi.org/10.3847/2515-5172/ac74c4) | 21 | More than 150 M light curves with T < 16, sectors 1–26. |
| Feinstein et al. 2019, PASP 131, 094502 — eleanor | [10.1088/1538-3873/ab291c](https://doi.org/10.1088/1538-3873/ab291c) | 241 | FFI extraction tool. |
| Fausnaugh et al. 2024, TESS Data Release Notes (e.g. Sector 79, DR111) | [10.64631/iyqc8924](https://doi.org/10.64631/iyqc8924) | – | Per-sector momentum dumps, scattered light and anomalies. Ingest them as data for the edge and dump tests. *(record only)* |

**Guerrero et al. 2021:**
- SPOC requires MES > 7.1, ≥ 2 transits and passing consistency vetoes.
- QLP requires BLS from 0.1 d to half the baseline, signal-to-pink-noise > 9 and BLS peak significance > 9.
- About 1200 SPOC TCEs per sector produce about 100 TOIs per sector.
- Neither pipeline searches for single transits on purpose.
- 565 of 2241 Prime Mission TOIs (about 25 %) turned out to be false positives.
- 169 community CTOIs became TOIs. All of them were SPOC or QLP TCEs that had been triaged out by mistake.

**Caldwell et al. 2020:**
- TESS-SPOC FFI processes up to 160k targets per sector.
- Field stars are included only to **T ≤ 13.5** (log g ≥ 3.5, crowding ≥ 0.8).
- Stars to T ≤ 16 are included only when "high value" (H ≤ 10 or d ≤ 100 pc).
- The T = 13.5–15 range is therefore not covered systematically.

## 3. Search algorithms and FFI searches

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Kovács, Zucker & Mazeh 2002, A&A 391, 369 — BLS | [10.1051/0004-6361:20020802](https://doi.org/10.1051/0004-6361:20020802) | 992 | Still QLP's engine. Basis of the experimental `gpu_bls.py`. |
| Hippke & Heller 2019, A&A 623, A39 — Transit Least Squares | [10.1051/0004-6361/201834672](https://doi.org/10.1051/0004-6361/201834672) | 250 | See the note after this table. |
| TLS documentation, FAQ ([readthedocs](https://transitleastsquares.readthedocs.io/en/latest/FAQ.html)) | – | – | Source of the "SDE 9 ≈ 10⁻⁴" mapping: SDE 7.0 → 1 %, 8.3 → 0.1 %, 9.1 → 0.01 % from more than 10k white-noise runs. The FAQ itself warns these numbers are too optimistic with red noise. |
| Heller, Hippke & Rodenbeck 2019, A&A 627, A66 — TLS survey II, 17 new planets from K2 | [10.1051/0004-6361/201935600](https://doi.org/10.1051/0004-6361/201935600) | 23 | Gate SDE ≥ 9 (false-positive rate < 10⁻⁴ only in the white-noise limit). Found 17 extra small planets in K2 systems already known to host planets: evidence for the "extra planets" niche. |
| Hippke et al. 2019, AJ 158, 143 — wōtan | [10.3847/1538-3881/ab3984](https://doi.org/10.3847/1538-3881/ab3984) | 242 | See the note after this table. |
| Ofir 2014, A&A 561, A138 — optimal period sampling | [10.1051/0004-6361/201220860](https://doi.org/10.1051/0004-6361/201220860) | 61 | Frequency grid uniform in f^(1/3). TLS already uses it; any BLS should too. |
| Kunimoto et al. 2023, QLP Data Release Notes 003 — GPU transit search | [arXiv:2302.01293](https://arxiv.org/abs/2302.01293) | – | See the note after this table. |
| Kunimoto et al. 2022, ApJS 259, 33 — the TESS Faint-star Search, 1617 TOIs | [10.3847/1538-4365/ac5688](https://doi.org/10.3847/1538-4365/ac5688) | 62 | See the note after this table. |
| Montalto et al. 2020, MNRAS 498, 1726 — DIAmante | [10.1093/mnras/staa2438](https://doi.org/10.1093/mnras/staa2438) | 43 | 976,814 FGKM stars, difference-imaging multi-sector FFI photometry, random forest. 396 candidates (252 new), light curves at MAST. A candidate list to mirror. |
| Melton et al. 2024a, b, AJ 167, 202 and 203 — DTARPS I and II | [10.3847/1538-3881/ad29f0](https://doi.org/10.3847/1538-3881/ad29f0), [10.3847/1538-3881/ad29f1](https://doi.org/10.3847/1538-3881/ad29f1) | 9 / 9 | Autoregressive search on 0.9 M light curves. 462 candidates plus 310 in the Galactic plane, 58 % previously unidentified. Mirror. |
| Caceres et al. 2019, AJ 158, 57 — Autoregressive Planet Search | [10.3847/1538-3881/ab26b8](https://doi.org/10.3847/1538-3881/ab26b8) | 29 | ARIMA residuals plus a transit comb filter, as an alternative to detrending followed by BLS. |
| Nardiello et al. 2019, 2020, MNRAS 490, 3806 and 495, 4924 — PATHOS | [10.1093/mnras/stz2878](https://doi.org/10.1093/mnras/stz2878), [10.1093/mnras/staa1465](https://doi.org/10.1093/mnras/staa1465) | 71 / 58 | PSF photometry with neighbors subtracted, for crowded fields and clusters. |
| Garcia et al. 2024, AJ 167, 284 — nuance | [10.3847/1538-3881/ad3cd6](https://doi.org/10.3847/1538-3881/ad3cd6) | 6 | On 438 fast-rotating TESS M dwarfs, a joint GP plus transit search beat every detrend-then-BLS combination in 93 % of cases. Candidate for the M-dwarf niche. |
| Aigrain & Foreman-Mackey 2023, ARA&A 61, 329 — Gaussian processes for time series | [10.1146/annurev-astro-052920-103508](https://doi.org/10.1146/annurev-astro-052920-103508) | 154 | Reference for GP detrending choices and costs. |
| Panahi & Zucker 2021, PASP 133, 024502 — Sparse BLS | [10.1088/1538-3873/abd9ab](https://doi.org/10.1088/1538-3873/abd9ab) | 9 | BLS with no phase grid; faster on sparse data. |
| Wang et al. 2024, MNRAS 528, 4053 — GPU phase folding plus deep learning | [10.1093/mnras/stae245](https://doi.org/10.1093/mnras/stae245) | 7 | About 1000× faster than BLS, aimed at P < 1 d. |
| Ment et al. 2026, AJ 172, 249 — GERBLS | [10.3847/1538-3881/aea0c8](https://doi.org/10.3847/1538-3881/aea0c8) | 0 | BLS based on the fast folding algorithm, O(n log n), 10–100× faster than brute force. Designed for large injection-recovery campaigns. |

**Hippke & Heller 2019:**
- **SDE 7 gives a 1 % false-positive rate** in white noise.
- At that threshold TLS recovers 93.1 % of small planets against 75.7 % for BLS.
- The paper does **not** state "SDE 9 ≈ 10⁻⁴". That mapping comes from the TLS documentation in the row below.

**Wōtan (Hippke et al. 2019):**
- The time-windowed biweight is best in most cases.
- The optimal window is about **3× the transit duration**.
- An adaptive window per star beats a fixed one.
- Splines are comparable when stellar variability is strong.
- GP detrending can carve dips around deep transits.

**Kunimoto et al. 2023 (QLP GPU search), current since sector 59:**
- GPU BLS with durations restricted to 0.5–2.0× the circular duration from TIC ρ\*.
- P_min where a = 2 R\*. P_max is the longest continuous stretch of data.
- Detection needs ≥ 2 transits, **S/N_pink > 9 and S/N > 9**.

**Kunimoto et al. 2022 (Faint-star Search):**
- Prime-mission QLP signals down to T = 13.5 were vetted automatically: 2.5 M BLS signals, then 686k after AstroNet triage, then **1617 new TOIs**.
- Noise on transit timescales is about 1000 ppm at T ≈ 13.5.
- Most faint-star TOIs orbit giants and are about 3.5× deeper than average.

## 4. Single and duo transits

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Osborn et al. 2016, MNRAS 457, 2273 — single transits from K2 | [10.1093/mnras/stw137](https://doi.org/10.1093/mnras/stw137) | 61 | Bayesian single-transit fit that gives a period posterior from duration, shape and ρ\*. The method for the monotransit branch. |
| Foreman-Mackey et al. 2016, AJ 152, 206 — long-period transiting planets | [10.3847/0004-6256/152/6/206](https://doi.org/10.3847/0004-6256/152/6/206) | 99 | Fully automated 1–2 transit search with efficiency measured by injection. Template for a monotransit detector with measured completeness. |
| Cooke et al. 2018, A&A 619, A175 — single transits in TESS | [10.1051/0004-6361/201834014](https://doi.org/10.1051/0004-6361/201834014) | 32 | For P ≳ 45 d, single transits outnumber multi-transit detections about 3:1. |
| Cooke et al. 2019, A&A 631, A83 — the extended mission and southern monotransits | [10.1051/0004-6361/201936703](https://doi.org/10.1051/0004-6361/201936703) | 15 | About 80 % of Year 1 monotransits transit again in Year 4, but 75 % of those only once, so the period stays aliased. |
| Cooke et al. 2021, MNRAS 500, 5088 — resolving monotransit period aliases | [10.1093/mnras/staa3569](https://doi.org/10.1093/mnras/staa3569) | 15 | About 400 duotransits with **about 38 aliases each**. A duotransit's period is a list P = ΔT/n, not a single value. |
| Villanueva, Dragomir & Gaudi 2019, AJ 157, 84 — single-transit yield | [10.3847/1538-3881/aaf85e](https://doi.org/10.3847/1538-3881/aaf85e) | 48 | 241 single transits at S/N ≥ 7.3 in 2-min data plus ≥ 977 in FFIs; 146 with period constrained to 10 % from photometry alone. |
| Gill et al. 2020, MNRAS 491, 1548 — NGTS and WASP recovery of a TESS single transit | [10.1093/mnras/stz3212](https://doi.org/10.1093/mnras/stz3212) | 22 | Archival ground photometry narrowed the period to 3 options. The object turned out to be an eclipsing binary: deep single events are often EBs. |
| Hawthorn et al. 2024, MNRAS 528, 1841 — TESS duotransit candidates | [10.1093/mnras/stad3783](https://doi.org/10.1093/mnras/stad3783) | 4 | `monofind`: 3 consecutive points more than 3 MAD below the median, with background and centroid rejection. 85 duotransits (60 new), T14 = 2–10 h. A cheap baseline detector, and a list to mirror. |
| Rodel et al. 2024, MNRAS 529, 715 — TIaRA yields from Years 1 and 3 | [10.1093/mnras/stae474](https://doi.org/10.1093/mnras/stae474) | 7 | Predicts about 3× more detectable planets with P > 25 d than the TOI catalog holds. Yield evidence for the long-period niche. |

## 5. Completeness, reliability and expected yield

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Christiansen et al. 2013, ApJS 207, 35 — Kepler signal recovery I | [10.1088/0067-0049/207/2/35](https://doi.org/10.1088/0067-0049/207/2/35) | 83 | Pixel-level injection: measured S/N = 0.997 × expected. Losses concentrate near gaps. Replicate the per-event S/N retention test for our detrending. |
| Christiansen et al. 2015, ApJ 810, 95 — Kepler signal recovery II | [10.1088/0004-637X/810/2/95](https://doi.org/10.1088/0004-637X/810/2/95) | 99 | Only **25.8 % recovery at MES 7.1**. Evaluating their fit gives about 62 % at 9, 76 % at 10 and 92 % at 12. A 90 % recall target at SNR 10 is above what Kepler achieved. |
| Christiansen et al. 2016, ApJ 828, 99 — Kepler signal recovery III | [10.3847/0004-637X/828/2/99](https://doi.org/10.3847/0004-637X/828/2/99) | 55 | Efficiency dropped above 40 d, partly from a wrongly implemented veto. Report recall in bins of period, S/N and number of transits. |
| Christiansen et al. 2020, AJ 160, 159 — Kepler signal recovery IV | [10.3847/1538-3881/abab0b](https://doi.org/10.3847/1538-3881/abab0b) | 44 | Clear penalty at the minimum number of transits. Expect a stronger one at 2–3 transits in TESS. |
| Burke et al. 2015, ApJ 809, 8 — terrestrial occurrence for GK dwarfs | [10.1088/0004-637X/809/1/8](https://doi.org/10.1088/0004-637X/809/1/8) | 365 | Per-target completeness from a gamma CDF in MES, the window function and per-target noise. Store σ on the transit timescale per target. |
| Burke & Catanzarite 2017, NASA technical reports — per-target detection contours for DR25 | NTRS | 3–4 | Flux-level injection is enough for per-target contours, and it is affordable. *(record only)* |
| Thompson et al. 2018, ApJS 235, 38 — Kepler DR25 catalog | [10.3847/1538-4365/aab4f9](https://doi.org/10.3847/1538-4365/aab4f9) | 430 | Reliability measured with **inverted and scrambled light curves**: 37.2 % reliable at low S/N and 200–500 d. Also the full Robovetter (section 6). |
| Sullivan et al. 2015, ApJ 809, 77 — TESS simulations | [10.1088/0004-637X/809/1/77](https://doi.org/10.1088/0004-637X/809/1/77) | 555 | Detection rule SNR ≥ 7.3 plus ≥ 2 transits. More than 1000 astrophysical false positives expected. |
| Barclay, Pepper & Quintana 2018, ApJS 239, 2 — revised TESS yield | [10.3847/1538-4365/aae3e9](https://doi.org/10.3847/1538-4365/aae3e9) | 298 | More than 10,000 planets around fainter FFI stars. Warns that planets with fewer than 3 transits are very hard to identify uniquely. |
| Kunimoto et al. 2022, AJ 163, 290 — TESS yield through Years 1–7 | [10.3847/1538-3881/ac68e3](https://doi.org/10.3847/1538-3881/ac68e3) | 48 | Detection probability P_det(S/N, N_transits) from Kepler DR25. 12,519 ± 678 planets through EM2, increasingly small, long-period and around faint stars. Use P_det as the expected-recall model. |
| Ment & Charbonneau 2023, AJ 165, 265 — terrestrial planets around nearby mid-to-late M dwarfs | [10.3847/1538-3881/acd175](https://doi.org/10.3847/1538-3881/acd175) | 69 | Per-star injection-recovery for 363 M dwarfs. Template for the M-dwarf niche. |

## 6. Vetting systems and diagnostics

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Coughlin et al. 2014, AJ 147, 119 — contamination in the Kepler field via ephemeris matching | [arXiv:1401.1240](https://arxiv.org/abs/1401.1240) | 99 | 12 % of KOIs (35 % after bias correction) were false positives from contamination. 77 % matched their parent at a 1:1 period, 19 % at 1:2. The source can be up to 5 mag fainter than the star it contaminates. Multi-planet systems: 2.4 % against 16 % for singles. |
| Bryson et al. 2013, PASP 125, 889 — background false positives from Kepler data | [arXiv:1303.0052](https://arxiv.org/abs/1303.0052) | 151 | PRF fit to the difference image, a **3σ** offset rule, offset against the catalog position in crowded fields, fit quality ≥ 0.7. |
| Rowe et al. 2015, ApJS 217, 16 — Kepler candidates V | [arXiv:1501.07286](https://arxiv.org/abs/1501.07286) | – | Origin of the model-shift uniqueness test. |
| Mullally et al. 2015, ApJS 217, 31 — Kepler candidates VI | [arXiv:1502.02038](https://arxiv.org/abs/1502.02038) | – | Argues against declaring false positives from inferred radius alone. |
| Coughlin et al. 2016, ApJS 224, 12 — Kepler candidates VII (DR24) | [arXiv:1512.06149](https://arxiv.org/abs/1512.06149) | 243 | Model-shift tests (primary vs red noise, tertiary and positive events). Flags signals dominated by one transit. Does not use stellar parameters. |
| Thompson et al. 2018, ApJS 235, 38 (same as section 5) | [10.3847/1538-4365/aab4f9](https://doi.org/10.3847/1538-4365/aab4f9) | 430 | Robovetter thresholds. **Ghost diagnostic** (halo/core ratio > 4). **Ephemeris match:** period and epoch differences < 5σ, period ratios up to 50, allowed distance growing with the parent's brightness. |
| Kostov et al. 2019, AJ 157, 124 — DAVE | [arXiv:1901.07459](https://arxiv.org/abs/1901.07459) | 59 | A centroid offset with only 2–3 transits, or one dominated by a bright field star, is "indeterminate", not a false positive. |
| Kunimoto et al. 2025, AJ 170, 280 — LEO-Vetter | [arXiv:2509.10619](https://arxiv.org/abs/2509.10619) | 8 | See the note after this table. |
| Bryson & Kunimoto 2025, RNAAS 9, 81 — Transit-APP | [10.3847/2515-5172/adcb3a](https://doi.org/10.3847/2515-5172/adcb3a) | 2 | Per-star positional probability from simulated difference images, without centroids. Usable as a prior in the FPP. |
| Burke, TESS-ExoClass (software, [GitHub](https://github.com/christopherburke/TESS-ExoClass)) | – | – | Kepler-style tests plus momentum-dump and centroid flags. No refereed paper; described in Guerrero 2021 §6. |
| Ross et al. 2024, MNRAS 528, 5160 — DEATHSTAR | [arXiv:2312.08373](https://arxiv.org/abs/2312.08373) | 6 | Uses ZTF and ATLAS archival images to locate the true eclipsing source. Possible deep-vetting add-on. |
| Eisner et al. 2021, MNRAS 501, 4669 — Planet Hunters TESS II | [10.1093/mnras/staa3739](https://doi.org/10.1093/mnras/staa3739) | 50 | Volunteers recover 85 % of TOIs above 4 R⊕. 90 new candidates, 73 of them single transits. Mirror the list. |

**LEO-Vetter (Kunimoto et al. 2025):**
- Open-source automated vetting for TESS: 91 % completeness, 97 % reliability against false alarms.
- Thresholds are in Appendix B: model-shift MS1–MS3, SWEET (sinusoidal variability), chases, mean-to-median depth, asymmetry, transit model vs line, odd-even timing, and an albedo check for weak secondaries.
- It assumes dilution-corrected input.
- 153 of 325 M-dwarf signals that passed flux-level vetting failed its centroid test.

## 7. False-positive probability and statistical validation

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Morton 2012, ApJ 761, 6 — automated validation | [arXiv:1206.1568](https://arxiv.org/abs/1206.1568) | 225 | The framework behind VESPA. |
| Morton et al. 2016, ApJ 822, 86 — FPPs for all KOIs | [arXiv:1605.02825](https://arxiv.org/abs/1605.02825) | 450 | FPP < 0.01 validates and FPP > 0.9 marks a likely false positive, but only with a positional probability > 0.99 on target. |
| Giacalone et al. 2021, AJ 161, 24 — TRICERATOPS | [arXiv:2002.00691](https://arxiv.org/abs/2002.00691) | 167 | See the note after this table. |
| Giacalone et al. 2022, AJ 163, 99 — validation of 13 TESS planets | [arXiv:2201.12661](https://arxiv.org/abs/2201.12661) | 36 | In practice validation combined ground follow-up, DAVE and TRICERATOPS *(abstract)*. |
| Gomez Barrientos et al. 2025, AJ 170, 148 — TRICERATOPS+ | [arXiv:2508.02782](https://arxiv.org/abs/2508.02782) | 7 | Same validation cut. Adds multi-band ground light curves to the FPP. |
| Díaz et al. 2014, MNRAS 441, 983 — PASTIS | [arXiv:1403.6725](https://arxiv.org/abs/1403.6725) | 169 | Strong support for the right hypothesis only at transit SNR > 50; below that, the answer depends on the priors. |
| Lissauer et al. 2012, ApJ 750, 112; Lissauer et al. 2014, ApJ 784, 44; Rowe et al. 2014, ApJ 784, 45 — multiplicity | [arXiv:1201.5424](https://arxiv.org/abs/1201.5424), [arXiv:1402.6352](https://arxiv.org/abs/1402.6352), [arXiv:1402.6534](https://arxiv.org/abs/1402.6534) | 296 / 207 / 450 | Candidates in multi-planet systems are much more likely to be planets (the "multiplicity boost"). Caveat: the second signal can come from a different, fainter star. |
| Valizadegan et al. 2023, AJ 166, 28 — multiplicity boost for classifiers | [arXiv:2305.02470](https://arxiv.org/abs/2305.02470) | 19 | Applies the boost to ML scores. |
| Mistry et al. 2023a, b; 2024 — VaTEST I–III (MNRAS 521, 1066; AJ 166, 9; PASA 41, e030) | [arXiv:2211.07957](https://arxiv.org/abs/2211.07957), [arXiv:2301.09865](https://arxiv.org/abs/2301.09865), [arXiv:2311.00688](https://arxiv.org/abs/2311.00688) | 12 / 13 / 10 | Validation workflows built on TRICERATOPS and VESPA, later with ground photometry and high-resolution imaging. |
| Magliano et al. 2023, MNRAS 519, 1562 — hot Neptunes in TESS | [arXiv:2211.08490](https://arxiv.org/abs/2211.08490) | 11 | DAVE then TRICERATOPS: 250 events gave 18 with FPP < 50 %, and only 2 validated after follow-up. |
| Santerne et al. 2012, A&A 545, A76; Santerne et al. 2016, A&A 587, A64 — giant-candidate false-positive rates | [arXiv:1206.0601](https://arxiv.org/abs/1206.0601), [arXiv:1511.00643](https://arxiv.org/abs/1511.00643) | 152 / 251 | 35 % of close-in giant candidates and 54.6 % of giants within 400 d were false positives. |
| Fressin et al. 2013, ApJ 766, 81 — the false-positive rate of Kepler | [10.1088/0004-637X/766/2/81](https://doi.org/10.1088/0004-637X/766/2/81) | 1150 | 9.4 % overall, 17.7 % for 6–22 R⊕. Context only: Kepler rates do not transfer to TESS (21″ pixels, fainter stars). |

**Giacalone et al. 2021 (TRICERATOPS):**
- **Validated:** FPP < 0.015 and NFPP < 10⁻³.
- **Likely planet:** FPP < 0.5 and NFPP < 10⁻³.
- **Likely nearby false positive:** NFPP > 0.1.
- These classes hold only for Rp < 8 R⊕, and work best at SNR > 15.
- With 30-min FFI data there is no region where planets can be validated confidently.
- The paper uses 10⁶ draws and repeats each case 20 times.

## 8. Machine learning and probability calibration

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Shallue & Vanderburg 2018, AJ 155, 94 — Astronet | [10.3847/1538-3881/aa9e09](https://doi.org/10.3847/1538-3881/aa9e09) | 368 | Global plus local view CNN. |
| Yu et al. 2019, AJ 158, 25 — Astronet-Triage | [10.3847/1538-3881/ab21d6](https://doi.org/10.3847/1538-3881/ab21d6) | 70 | Triage reaches 97 % average precision; vetting only 69 %. Separating planets from EBs is the hard part. |
| Osborn et al. 2020, A&A 633, A53 — ML on simulated TESS data | [arXiv:1902.08544](https://arxiv.org/abs/1902.08544) | 56 | Trained on simulations, it recovered only 61 % of real TOIs. Do not train on injections alone. |
| Olmschenk et al. 2021, AJ 161, 273 — CNN on FFI light curves | [10.3847/1538-3881/abf4c6](https://doi.org/10.3847/1538-3881/abf4c6) | 27 | A CNN run directly on FFI light curves. |
| Tey et al. 2023, AJ 165, 95 — Astronet-Triage-v2 | [10.3847/1538-3881/acad85](https://doi.org/10.3847/1538-3881/acad85) | 23 | QLP's current triage: 99.6 % recall at 75.7 % precision. The baseline to beat in Phase 5. |
| Valizadegan et al. 2022, ApJ 926, 120 — ExoMiner | [10.3847/1538-4357/ac4399](https://doi.org/10.3847/1538-4357/ac4399) | 71 | Validated 301 new Kepler planets using DV-style diagnostics as inputs. |
| Valizadegan et al. 2025, AJ 170, 287 — ExoMiner++ for 2-min TESS | [10.3847/1538-3881/ae03a4](https://doi.org/10.3847/1538-3881/ae03a4) | 2 | 7330 planet candidates among 147,568 TCEs, 50 of them new CTOIs. Calls TESS labels noisy. Mirror the catalog. |
| Fiscale et al. 2025, AJ 170, 73 — DART-Vetter | [arXiv:2506.05556](https://arxiv.org/abs/2506.05556) | 3 | Compact light-curve-only CNN, 91 % recall; generalizes best at high S/N and P < 50 d. |
| Salinas et al. 2025, MNRAS 538, 2031 — transformer for FFI candidates | [10.1093/mnras/staf347](https://doi.org/10.1093/mnras/staf347) | 4 | No periodicity assumed: 214 new candidates in sectors 1–26, 88 of them single transits. Mirror. |
| Armstrong et al. 2021, MNRAS 504, 5327 — ML validation of 50 Kepler planets | [arXiv:2008.10516](https://arxiv.org/abs/2008.10516) | 43 | Calibrate on held-out folds. Validating at p > 0.99 needs about 1 % calibration precision. Flag outliers, evolved hosts and companions. Never validate with one method alone. |
| Niculescu-Mizil & Caruana 2005, ICML — predicting good probabilities | [10.1145/1102351.1102430](https://doi.org/10.1145/1102351.1102430) | 1291 | Platt (logistic) scaling beats isotonic regression below about 200–1000 calibration cases. |
| Zadrozny & Elkan 2002, KDD — calibrated multiclass probabilities | [10.1145/775047.775151](https://doi.org/10.1145/775047.775151) | 963 | Isotonic calibration. |

## 9. Catalogs and stellar data

| Reference | ID | Cites | Take for PlanetHunter |
|---|---|---|---|
| Stassun et al. 2018, AJ 156, 102; Stassun et al. 2019, AJ 158, 138 — TIC and TIC v8 | [arXiv:1706.00495](https://arxiv.org/abs/1706.00495), [arXiv:1905.10694](https://arxiv.org/abs/1905.10694) | 663 / 1044 | R\*, M\*, Teff, Tmag. The contamination ratio is contaminant flux over target flux within a Tmag-dependent radius; it is not aperture-specific. |
| Paegert et al. 2021, TIC 8.1 and 8.2 — phantoms | [arXiv:2108.04778](https://arxiv.org/abs/2108.04778) | – | About 34 M fixes in 8.2 (artifact, join and split phantoms). Respect the TIC duplicate and artifact flags. |
| Gaia Collaboration, Vallenari et al. 2023, A&A 674, A1 — Gaia DR3 | [arXiv:2208.00211](https://arxiv.org/abs/2208.00211) | 4439 | Citation for neighbors and stellar data. |
| Fabricius et al. 2021, A&A 649, A5 — Gaia EDR3 validation | [arXiv:2012.06242](https://arxiv.org/abs/2012.06242) | 397 | Pair completeness drops below 0.7″. Use `ipd_frac_multi_peak` as a flag. Map DR2 to DR3 with `dr2_neighbourhood`; never assume the ID carried over. |
| Belokurov et al. 2020, MNRAS 496, 1922 — unresolved companions from Gaia astrometry | [arXiv:2003.05467](https://arxiv.org/abs/2003.05467) | 374 | RUWE flags unresolved companions; the threshold is ours to calibrate. |
| Mowlavi et al. 2023, A&A 674, A16 — Gaia DR3 eclipsing binaries | [arXiv:2211.00929](https://arxiv.org/abs/2211.00929) | 123 | 2.18 M EB candidates to G = 20, only 25–50 % complete. Absence from it is weak evidence. |
| Prša et al. 2022, ApJS 258, 16 — TESS eclipsing binaries I | [arXiv:2110.13382](https://arxiv.org/abs/2110.13382) | 213 | 4584 EBs from 2-min data in sectors 1–26 only. |
| Kostov et al. 2025, ApJS 279, 50 — TESS Ten Thousand EB catalog | [arXiv:2506.05631](https://arxiv.org/abs/2506.05631) | 22 | 10,001 vetted FFI EBs from sectors 1–82, plus about 900k unvetted detections with network score > 0.9 usable as a soft flag. |
| Ziegler et al. 2020, AJ 159, 19; Ziegler et al. 2021, AJ 162, 192 — SOAR TESS survey | [arXiv:1908.10871](https://arxiv.org/abs/1908.10871), [arXiv:2103.12076](https://arxiv.org/abs/2103.12076) | 250 / 59 | About 15–20 % of TESS hosts have a companion within 3″, which dilutes depths and inflates FPP. |
| Akeson et al. 2013, PASP 125, 989 — NASA Exoplanet Archive | [arXiv:1307.2944](https://arxiv.org/abs/1307.2944) | 806 | Superseded as the citation (next row). |
| Christiansen et al. 2025, PSJ 6, 186 — the NASA Exoplanet Archive and ExoFOP | [arXiv:2506.03299](https://arxiv.org/abs/2506.03299) | 168 | The current citation for both the Archive and ExoFOP. |
| Schneider et al. 2011, A&A 532, A79 — exoplanet.eu | [arXiv:1106.0586](https://arxiv.org/abs/1106.0586) | 586 | Inclusion criteria are deliberately loose and include unconfirmed candidates. Map its statuses to our classes carefully. |

## 10. Community rules and live sources (accessed 2026-10-09)

| Source | Take for PlanetHunter |
|---|---|
| ExoFOP-TESS news ([news.php](https://exofop.ipac.caltech.edu/tess/news.php)) | See the notes after this table. |
| ExoFOP candidate guidelines ([help.php](https://exofop.ipac.caltech.edu/tess/help.php)) | A signal at an integer multiple of a known period is attached to the existing object, not submitted as a new one. |
| NASA Exoplanet Archive TOI columns ([docs](https://exoplanetarchive.ipac.caltech.edu/docs/API_TOI_columns.html)) | `tfopwg_disp` codes are APC, CP, FA, FP, KP and PC. The table syncs from ExoFOP about **once a week**, so the ExoFOP CSV is the source of truth for the 48 h freshness rule. |
| Archive TAP, `toi` grouped by disposition (run 2026-10-09) | PC 4824, APC 488, CP 814, KP 606, FP 1314, FA 100. False positives are about half of the TOIs with a definitive disposition. |
| Gaia DR4 ([ESA news 2026](https://www.cosmos.esa.int/web/gaia/news-2026)) | Planned for 2 December 2026: 5.5 years of data, epoch photometry, about 130 data products. |
| PLATO ([ESA](https://www.esa.int/ESA_Multimedia/Videos/2026/03/Plato_s_launch_on_Ariane_6)) | Launch planned for early 2027 (ESA gives January 2027). |
| TESS extended mission 3 ([planning guide](https://heasarc.gsfc.nasa.gov/docs/tess/docs/Guide-to-TESS-for-EM-planning.pdf), [ExoPAG 32 update](https://exoplanets.nasa.gov/internal_resources/3340/ExoPAG32-1230_Youngblood_TESS_Mission_Update.pdf)) | September 2025 to September 2028, with a budget about 30 % smaller from October 2025. |

**ExoFOP-TESS news:**
- Candidate uploads were paused on 2026-03-31 and reopened on 2026-08-19.
- A candidate must now **be published in a peer-reviewed journal first**.
- Uploading requires approval, requested through a form.

## 11. Recent preprints (not refereed; indicative only)

| Reference | ID | Take for PlanetHunter |
|---|---|---|
| Collier et al. 2026 — high-resolution imaging and statistical validation of TESS candidates | [arXiv:2608.21560](https://arxiv.org/abs/2608.21560) | 72 % of 68 imaging-dependent validations fail without their contrast curve; 100 % below 1.7 R⊕. Without imaging, our FPP cannot validate small planets. |
| Martinho et al. 2026 — ExoMiner++ 2.0 for FFI | [arXiv:2601.14877](https://arxiv.org/abs/2601.14877) | FFI vetting catalog; mirror once released. |
| Dévora-Pajares et al. 2025 — WATSON-Net | [arXiv:2511.08768](https://arxiv.org/abs/2511.08768) | Ten calibrated cross-validation models; TESS precision 0.93, recall 0.76. |
| Hu et al. 2026 — GTLS, GPU-accelerated TLS | [arXiv:2607.00348](https://arxiv.org/abs/2607.00348) | 24× faster than CPU TLS on 3000-day curves, recall 79.4 % against 81.1 %. Only relevant for long multi-sector searches. |
| Tschudi 2026a, A&A 710, A352 (refereed) and 2026b — M-dwarf transit surveys | [10.1051/0004-6361/202659754](https://doi.org/10.1051/0004-6361/202659754), [arXiv:2609.04887](https://arxiv.org/abs/2609.04887) | On active M dwarfs, candidate SDE often sits at the per-star noise floor. The false-alarm rate falls from 79 % to 0.6 % as the S/N_pink floor rises from 6 to 8. Single-author; supports per-target empirical floors. |
| Littlefield et al. 2026 — TESS sensitivity in TOIs with close companions | [arXiv:2608.13527](https://arxiv.org/abs/2608.13527) | Sensitivity to planets around the secondary star is very low. Include dilution in completeness. |
| Ulmer-Moll et al. 2026 — long-period transiting exoplanets, review | [arXiv:2604.09254](https://arxiv.org/abs/2604.09254) | Read before designing the monotransit flow *(abstract)*. |
