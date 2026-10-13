# PlanetHunter

## Language

- All code, comments, docstrings, CLI and log messages, and repository documents are in English.
- The study site is trilingual: English (default), Spanish and Portuguese, under `study-site/docs/{en,es,pt}`. New or changed lessons go into all three languages (see `study-site/STYLE.md`).
- The project owner (Vitor) prefers to chat in Brazilian Portuguese; answer him in pt-BR, but write repository content in English.

Exoplanet search system for public data (TESS first) with automated vetting, crossmatch against catalogs of known planets, and alerts only for new candidates.

- Full plan: [docs/PLAN.md](docs/PLAN.md)
- Master prompt (persona, domain truths, rules): [docs/EXPERT_PROMPT.md](docs/EXPERT_PROMPT.md). Read it before any scientific task.
- Literature basis: [docs/LITERATURE.md](docs/LITERATURE.md). Cite it when choosing a method or threshold; the backlog derived from it is PLAN §17.
- Beginner's guide (the user is a layperson in astronomy): [docs/BEGINNERS_GUIDE.md](docs/BEGINNERS_GUIDE.md). Update it whenever a pipeline step changes.
- Agents: `.claude/agents/`. Skills: `.claude/skills/`.

## Stack

Python 3.12 + `uv`. `ruff` for lint/format, `pytest` for tests. Astro: `lightkurve`, `astroquery`, `astropy`, `wotan`, `transitleastsquares`, `triceratops`, `batman`. Data: Parquet (float32) + DuckDB. CLI with `typer`. Orchestration: cron/Task Scheduler at first, Prefect 3 later.

## Target layout

```
src/planethunter/
  ingest/      # MAST, lightkurve, TESScut, HLSP -> Parquet
  preprocess/  # quality mask, outliers, detrending (wotan), CBV
  search/      # TLS/BLS, single transits, multi-sector
  vetting/     # 13 tests, centroid, triceratops, score
  catalogs/    # local mirrors (Archive, TOI, CTOI, exoplanet.eu, EB cat)
  crossmatch/  # ID, cone+PM, period aliases, classes
  alerts/      # dossier, Telegram/Discord, digests
  db/          # DuckDB schema, migrations
  cli.py
tests/         # unit + benchmark (recall on known TOIs)
data/          # gitignored: raw/, parquet/, mirrors/, dossiers/
docs/
```

## Commands

```
uv sync
uv run pytest
uv run ruff check . && uv run ruff format .
uv run planethunter --help
uv run planethunter run-sector <N> --limit 2000   # end to end, simulated alerts
```

## Domain invariants (non-negotiable)

- Vocabulary: signal → candidate → CTOI → TOI → validated → confirmed. Never "discovery".
- Alert only after a complete crossmatch against fresh mirrors, re-checked at send time: ExoFOP TOI/CTOI and the NASA Exoplanet Archive < 48 h; slower catalogs by their own policy in `config/thresholds.yaml` (exoplanet.eu and K2 7 d, Kepler KOI 30 d, static VizieR catalogs by version). P0 on an already cataloged object = critical bug, open an issue.
- No network calls in the batch path (preprocess, search, basic vetting, crossmatch). Network only in ingestion, mirror sync and per-candidate deep vetting (triceratops, TPF), always with cache; without network the candidate stays pending, never approved.
- Crossmatch: an object is known only if it matches the star **and** the signal (period with aliases, or ≥ 50 % of individual transits coinciding with known ephemerides with a binomial chance probability < 1 %; near-misses stay `NEW`, flagged and capped at P2). Known host with a new period = `NEW` with `host_known`.
- Without deep vetting (TPF, Gaia, FPP) the severity ceiling is P1.
- Thresholds live in `config/thresholds.yaml`, versioned. Changing search/vetting requires rerunning `tests/benchmark` and attaching before/after.
- Units: time in BTJD, period in days, depth in ppm, radius in R⊕, separation in arcsec. `astropy.units` at module boundaries.
- Provenance on every `signals` row: sector, author, pipeline_version, run_id.

## Code conventions

- One stage = pure functions with DataFrame/Parquet input/output. No global state.
- Every function that touches the network: timeout, retry with exponential backoff, disk cache. A failure on one target does not bring down the batch.
- Structured (JSON) logs always with `tic_id`, `sector`, `run_id`.
- Flux in float32; time in float64.
- Annotated types; short docstring with units.

## Definition of done

Tests passing, recall benchmark without regression, `ruff` clean, module docs updated, provenance recorded.

## Agent workflow

The main session orchestrates. `astro-domain-expert` validates the science → the area engineer implements → `qa-benchmark-engineer` measures → `/code-review`. To locate code use `cavecrew-investigator`; for small edits `cavecrew-builder`.
