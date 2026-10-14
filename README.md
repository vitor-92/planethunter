# PlanetHunter

Automated search for exoplanet candidates in public data (TESS), with false-positive vetting, crossmatch against catalogs of known planets and candidates, and alerts only for what is new.

> **A note from the author.** I had never worked on, or even studied, astronomy or exoplanets before this. I am building PlanetHunter precisely to learn while I build it XD. That is why the repository comes with a [beginner's guide](docs/BEGINNERS_GUIDE.md), a [study plan](docs/STUDY_PLAN.md) and a whole [study site](study-site/README.md): they are the path I am following myself. Expect rough edges, and treat every result as a candidate to be checked, never as a discovery. Corrections and suggestions from people who know the field are very welcome.

- [System plan](docs/PLAN.md)
- [Expert prompt](docs/EXPERT_PROMPT.md)
- [Literature basis](docs/LITERATURE.md): the verified papers behind every design choice, and what each one means for the pipeline
- **[Beginner's guide](docs/BEGINNERS_GUIDE.md): how each analysis works, how to read results, what to study**
- **[Study plan](docs/STUDY_PLAN.md): basic, intermediate and advanced, with hands-on practice in the tool**
- Project rules for Claude Code: [CLAUDE.md](CLAUDE.md)
- Recall benchmarks: [docs/benchmarks/](docs/benchmarks/)

## Languages

The repository (code, comments, CLI and log messages, documentation) is in English. The companion study site is trilingual: English (default), Spanish and Portuguese, under `study-site/docs/{en,es,pt}` (how to run and publish it: [study-site/README.md](study-site/README.md)).

## Status

| Phase | State |
|---|---|
| 0. Foundation | done: `uv`, `ruff`, `pytest`, versioned config, DuckDB, CLI |
| 1. Baseline search | done: SPOC 2-min ingestion, per-sector adaptive detrending (robust red-noise ratio), parallel iterative TLS with TESS limb darkening, physical T14 and SNR measured by the pipeline (TLS fill-factor bias removed), S/N_pink, alias refinement, QLP period range (a ≥ 2R\* to 0.9× span). Recall 91.1 % on detectable TOIs in sector 69, unchanged after the 2026-10-10 fixes ([report](docs/benchmarks/2026-10-10-s0069-nogit.md)). Null runs (inverted/scrambled) for the false-alarm rate |
| 2. Crossmatch | done: 12 mirrors with per-source freshness (Archive, TOI, CTOI, exoplanet.eu, Kepler KOI, K2, TESS EB catalogs, DIAmante, DTARPS, LEO-Vetter, ExoMiner++), TIC + cone with proper motion, aliases with phase, integer harmonics, transit-by-transit matching with a binomial chance test, run-level epoch-spike and shared-signal (blend/duplicate) detection, re-check at send time |
| 3. Vetting + alerts | done: basic offline vetting (detection gates, period halving, odd-even, secondary, shape, limb-darkened fit with KDR25, radius, duration, centroid, edges, consistency) with veto/hard/soft verdict; deep vetting (difference image vs catalog position, Gaia neighbors with PSF dilution, Gaia EB, SIMBAD, other sectors, triceratops FPP/NFPP with repeats); calibrated `p_rank`/`p_abs` that can only lower priority; P0 only in the Giacalone et al. 2021 validation region; HTML dossier; Telegram/Discord with dry-run; human review. Pass rates and model metrics in the [sector 69](docs/benchmarks/2026-10-09-s0069-vetting.md) and [sector 107](docs/benchmarks/2026-10-09-s0107-run.md) reports were measured before the 2026-10-10 audit fixes; after them: [rerun report](docs/benchmarks/2026-10-13-rerun-after-audit.md) (sectors 69 and 107, null runs, model metrics, deep vetting of 241 sector-107 candidates: 0 P0, 0 P1, 61 P2) |
| 4–5 | not started (FFI of faint stars, single transits, injection-recovery, ML) |

**Version 1.0.0** (2026-10-09): full pipeline running on entire sectors. **2026-10-10/13:** code audit against the [literature](docs/LITERATURE.md), all fixes implemented ([PLAN §17](docs/PLAN.md)).

## Usage

```
uv sync
(cd tools/fpp && uv sync)                      # isolated triceratops environment (FPP)
uv run planethunter mirrors sync                 # catalog mirrors (exoplanet.eu takes minutes)
uv run planethunter mirrors status
uv run planethunter run-target 261136679          # end to end for one target (Pi Men)
uv run planethunter ingest sector 70 --limit 100  # SPOC 2-min light curves for a sector
uv run planethunter search --sector 70            # parallel TLS; prints run_id
uv run planethunter crossmatch <run_id>
uv run planethunter vet <run_id>                  # basic vetting + per-class validation + candidates
uv run planethunter candidates <run_id>           # approved NEW candidates, by severity
uv run planethunter vet-deep <run_id>             # TPF, Gaia, SIMBAD, other sectors, FPP (network)
uv run planethunter alert <run_id> [--send]       # dossiers + alerts (dry-run into data/outbox/ without --send)
uv run planethunter review <signal_id> rejected --reason eb   # records a human review
uv run planethunter run-sector 70 --limit 2000   # everything end to end
uv run planethunter benchmark build 69 && uv run planethunter benchmark run 69
```

Rejection reasons for `review --reason`: `eb`, `blend`, `systematic`, `noise`, `already_known`, `other`.

Data lives in `data/` (gitignored); change it with `PLANETHUNTER_DATA`.

To limit CPU use, set `PLANETHUNTER_MAX_WORKERS` (environment or `.env`): it caps every analysis pool (search, vetting, deep vetting), even over `--workers`, and each process runs one BLAS/OpenMP thread, so the value is the number of cores used. Example `.env` line: `PLANETHUNTER_MAX_WORKERS=6`. Thresholds in [config/thresholds.yaml](config/thresholds.yaml).

Real alerts: create `.env` at the repository root (already ignored by git) with `TG_TOKEN` and `TG_CHAT_ID` and/or `DISCORD_WEBHOOK`, and run with `--send`.

## Tests

```
uv run pytest              # offline, ~45 s
uv run pytest -m network   # downloads Pi Men from MAST and recovers Pi Men c
```

## License

Code and documentation are released under the [MIT License](LICENSE). The TESS data and the catalogs the pipeline downloads keep their own terms (see below).

## Credits and citation

PlanetHunter uses only public data and open software. If you use this code or its results, please cite the sources:

- **TESS**: a NASA mission (Explorer program). Data obtained from MAST (Mikulski Archive for Space Telescopes) at the Space Telescope Science Institute.
- **NASA Exoplanet Archive**, operated by Caltech under contract with NASA (Exoplanet Exploration Program).
- **ExoFOP-TESS** (TOI and CTOI lists) and the TESS Follow-up Observing Program.
- **Gaia** (ESA), via VizieR/CDS; **SIMBAD** (CDS, Strasbourg).
- TESS eclipsing binary catalog (Prša et al. 2022) and the Gaia DR3 eclipsing binary catalog.
- Software: Lightkurve, Astropy, astroquery, wotan (Hippke et al. 2019), Transit Least Squares (Hippke & Heller 2019), triceratops (Giacalone et al. 2021), NumPy, pandas, DuckDB.

Candidates produced by this tool are **not** discoveries: they are signals that need human review, submission as a CTOI and follow-up by other telescopes.
