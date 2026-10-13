# Using PlanetHunter

<p class="meta">Lab · from lesson B5 on · keep it handy</p>

!!! abstract "On this page you will learn"
    - How to install PlanetHunter and check that it works.
    - What each command does, when to use it and what it prints.
    - How to run your first TESS sector, at a small scale, from download to a simulated alert.
    - Where the files live and how to set up Telegram alerts safely.

This is the tool's pocket manual. It uses the vocabulary from the lessons: **signal** (a periodic dip found by the search), **candidate** (a new signal that passed vetting), **dossier** (the HTML report for a signal). If a term looks unfamiliar, check the [glossary](../glossary.md).

## Installation

You need **uv** and **Git**. If you have not installed them yet, follow the step-by-step guide in the [programming track](../programming/index.md). Open PowerShell (in VS Code: **Terminal > New Terminal**) and run:

```powershell
cd ~
git clone https://github.com/vitor-92/planethunter.git planethunter
cd planethunter
uv sync
```

If you got the project folder some other way, just go into it with `cd` and run `uv sync`.

`uv sync` reads the `pyproject.toml` file, downloads Python 3.12 if it is missing and installs all the libraries in a `.venv` folder inside the project. It takes a few minutes the first time.

The **FPP** calculation (false positive probability, lesson A3) uses the triceratops library, which needs old versions of NumPy. That is why it lives in a separate environment:

```powershell
cd tools\fpp
uv sync
cd ..\..
```

Check the installation:

```powershell
uv run planethunter --help
uv run pytest
```

The first one shows the list of commands. The second runs the automatic tests, with no internet, in about 45 seconds. All green: you are ready.

!!! note "Always put `uv run` in front"
    `uv run planethunter ...` makes sure the command uses the project's Python and libraries. Always run it from inside the `planethunter` folder. Every command accepts `--help`, for example `uv run planethunter search --help`.

## Command map

The pipeline has 8 steps (guide, section 1). Each command covers one or more of them.

| Command | Step | Uses the internet? | When to use it |
|---|---|---|---|
| `mirrors sync` / `mirrors status` | 0. Mirrors | sync: yes | Before any crossmatch; status whenever you want to check |
| `ingest sector` / `ingest target` | 1. Ingestion | yes | Download light curves |
| `search` | 2 and 3. Cleaning and search | no | Look for signals in light curves already downloaded |
| `crossmatch` | 4. "Does it already exist?" | no | After `search` |
| `vet` | 5. Basic vetting | no | After `crossmatch` |
| `vet-deep` | 6. Deep vetting | yes | For the candidates that passed `vet` |
| `calibrate` | 5 (model) | no | Train the calibrated planet probability from known signals |
| `candidates` | 7 | no | See the candidate queue |
| `dossier` | 7 | no | Generate the report for a signal |
| `alert` | 7 | only with `--send` | Generate dossiers and alert on P0/P1 |
| `review` | after 7 | no | Record your decision about a candidate |
| `run-target` | 1 to 4 | yes | Study a single star, end to end |
| `run-sector` | 0 to 7 | yes | Run everything on a sector |
| `benchmark build` / `benchmark run` | measurement | yes | Measure recall before and after changing something |

The project's rule is: **no internet in the critical path of the search**. The `search`, `crossmatch` and `vet` commands only work with local copies.

## Each command

### `mirrors sync` and `mirrors status`

```powershell
uv run planethunter mirrors sync
uv run planethunter mirrors status
```

`sync` downloads 12 lists of known objects: the NASA Exoplanet Archive, the ExoFOP TOIs and CTOIs, exoplanet.eu, the Kepler KOI table, the K2 planets and candidates, two TESS eclipsing binary catalogs (Prša et al. 2022 and Kostov et al. 2025) and four published candidate lists (DIAmante, DTARPS, LEO-Vetter and ExoMiner++). The published tables never change, so `sync` skips them once they are on disk (`--force` downloads them again). exoplanet.eu takes a few minutes. `status` shows, for each copy, its state, its age limit, its age, the number of rows, the start of its checksum and the file:

```text
archive_pscomppars   ok         <48 h age=   4.1 h rows=   6445 sha256=0833b7792d0f 20261009T193948Z.parquet
exoplanet_eu         ok        <168 h age=   4.1 h rows=   8354 sha256=a39d6af4196b 20261010T054524Z.parquet
toi                  ok         <48 h age=   4.1 h rows=   8151 sha256=fd7a3f98832d 20261009T193908Z.parquet
ctoi                 ok         <48 h age=   4.1 h rows=   5138 sha256=5a5e207dec9a 20261010T055318Z.parquet
eb_catalog           ok        static age=   3.9 h rows=   4584 sha256=d839230f8fce 20261009T194915Z.parquet
koi_cumulative       ok        <720 h age=   4.1 h rows=   9564 sha256=f9e3f26e63bc 20261010T054440Z.parquet
...
```

Each source has its own limit: 48 hours for the lists that change every day (TOI, CTOI, the Archive), 7 days (168 h) for exoplanet.eu and K2, 30 days (720 h) for the KOIs; `static` tables never expire. `STALE` means older than the limit. `MISSING` means the copy does not exist. `VERSION` means the copy on disk was made by an older version of the code and must be synced again. In all three cases, no signal can be classified as `NEW`: it becomes `UNVERIFIED` and does not generate an alert, and the command ends with an error code.

### `ingest sector` and `ingest target`

```powershell
uv run planethunter ingest sector 69 --limit 200
uv run planethunter ingest sector 69 --tics 100100827,261136679
uv run planethunter ingest target 261136679 --sectors 1,4,8
```

`ingest sector` downloads the 2-minute SPOC light curves for a sector. Options: `--limit N` (only the first N targets, for testing), `--tics` (comma-separated list of TICs, no spaces) and `--workers` (simultaneous downloads, default 8; be gentle with MAST). `ingest target` downloads all sectors of one star, or only those in `--sectors`.

Files already downloaded are skipped. At the end a summary appears with the counts `ok`, `skipped` and `errors`. Errors on one target do not bring down the others; the first ones are listed as `ERROR`.

### `search`

```powershell
uv run planethunter search --sector 69
```

Cleans the light curves, removes the star's slow variation and runs the TLS search in parallel. You must give `--sector` or `--tics`. Other options: `--all-sectors` (stitches all sectors of each target), `--workers` (parallel processes; the default uses all cores but one), `--resume <run_id>` (resumes an interrupted search, skipping the targets already done) and `--null inverted` or `--null scrambled` (a **null run**: the same search on light curves turned upside down or with each orbit shifted in time, to count false alarms; lesson [A1](../advanced/a1-detection-algorithms.md)).

To cap the number of CPU cores for every command, put `PLANETHUNTER_MAX_WORKERS=4` (or any number) in the `.env` file (see "Telegram alerts" below) or set it in the terminal: `$env:PLANETHUNTER_MAX_WORKERS = "4"`. It limits `search`, `vet`, `vet-deep` and `calibrate`, even when `--workers` asks for more.

The output is one line:

```text
run_id=20261009T204130Z-single-s69 targets=2164 done=2164 signals=887 errors=0 time=0.8 min
```

Keep the **run_id**. It identifies the run and is the input to the next commands. The format is the date and time in UTC, the mode (`single` for one sector, `multi` for several) and the sector (`s69`, or `sx` when there are several).

### `crossmatch`

```powershell
uv run planethunter crossmatch 20261009T204130Z-single-s69
```

Compares each signal with the mirrors and prints how many fell into each class: `NEW`, `KNOWN_PLANET`, `KNOWN_TOI`, `KNOWN_CTOI`, `KNOWN_PUBLISHED`, `KNOWN_FP`, `NEARBY_KNOWN` or `UNVERIFIED` (guide, step 4). Lots of `NEW` is normal: almost all of them are noise or defects that no catalog records. If the run has no signals, it prints `no signals`.

It also runs two checks across the whole run, stored with each signal: `epoch_spike_frac` (the fraction of its transits that fall on moments when many unrelated stars "transit" at once) and the shared-signal role (`source`, `victim` or `duplicate`, when another target within 2′ has the same period and transit time). Lesson [A2](../advanced/a2-mission-vetting.md) explains both.

### `vet`

```powershell
uv run planethunter vet 20261009T204130Z-single-s69
```

Runs the basic vetting tests, with no internet, on signals with an SDE of at least 9. A signal fails with any veto, any hard fail or more than one soft fail (lesson [M5](../intermediate/m5-vetting-in-practice.md)). Then it uses the crossmatch class to promote to candidates only the approved `NEW` signals. It prints three things: how many signals were tested (`signals vetted: ...`); the **validation table** (columns `class`, `n`, `pass`, `pass_rate`, `common_failures`, `vetoes`); and how many candidates there are by severity, such as `candidates: 3 {'P2': 3}`.

Use the validation table as a thermometer. `KNOWN_PLANET` should pass about 80 %. `KNOWN_FP` should pass little. If that changes a lot, something in the vetting has changed.

If a calibrated model exists (see `calibrate` below), `vet` also computes each signal's `p_rank` and `p_abs`.

### `vet-deep`

```powershell
uv run planethunter vet-deep 20261009T204130Z-single-s69
uv run planethunter vet-deep 20261009T204130Z-single-s69 --workers 2
uv run planethunter vet-deep 20261009T204130Z-single-s69 --force
```

Deep vetting, only for the candidates: a difference image on the pixels (TPF), Gaia neighbors and binaries, the star's type in SIMBAD, the presence of the signal in other sectors and FPP with triceratops. It uses the internet and stores what it downloads in `data/cache/`. The FPP runs 3 times per candidate, about 6 minutes each. Without a `run_id`, it processes all the candidates in the database. It prints `signal_id`, `verdict`, `score` and `failed` for each one, or `no candidates`.

It runs in parallel and can be resumed. `--workers` sets how many candidates are processed at the same time (the default comes from `vetting.deep_workers` in `config/thresholds.yaml`, currently 4). Each candidate is saved as soon as it finishes, so if the command is interrupted, running it again skips the candidates already evaluated. `--force` also redoes those.

### `calibrate`

```powershell
uv run planethunter calibrate
uv run planethunter calibrate --runs 20261009T204130Z-single-s69 --workers 4
```

Trains the **probability of being a planet** used to rank the queue (lesson A4). It takes the basic vetting results of signals whose answer is already known: `KNOWN_PLANET` (label 1), `KNOWN_FP` (label 0) and, when there are null runs, every signal they produced (label 0, false alarms by construction). Then it fits a logistic regression to the test results and calibrates it. Options: `--runs` (comma-separated run_ids; by default, the latest run of each sector that has labeled signals), `--null-runs` (by default, the latest null run of each sector; `none` skips them), `--recompute` (vets those runs again with the current code instead of using the stored results; no database writes), `--workers` (processes for `--recompute`, default 2), `--dry-run` (trains and reports, saves nothing) and `--repromote` (after saving, recomputes `p_rank` and `p_abs` and the severities of those runs).

It prints the cross-validation, grouped by star so the same star is never in both training and test, comparing the model with the deterministic vetting score, and then the two thresholds the severity uses:

```text
C = ... ; nested out-of-fold: ROC-AUC model ... vs score ... | PR-AUC model ... vs score ... | Brier ...
operating points: P2 cut ... (recall ..., FPR ...); P1 cut ... (recall ..., FPR ...)
model ... saved to .../data/models/vetting_lr.json
```

ROC-AUC measures how well a number separates planets from false positives (1.0 is perfect, 0.5 is a coin toss). On 338 known signals from sectors 69 and 107, the first version of the model reached 0.97, against 0.90 for the score. The **P2 cut** keeps 90 % of the known planets; the **P1 cut** allows at most 1 % false positives. The model is saved in `data/models/vetting_lr.json`, with its version and the runs it came from, and is used the next time you run `vet`.

### `candidates`

```powershell
uv run planethunter candidates 20261009T204130Z-single-s69
uv run planethunter candidates
```

Shows the queue of `NEW` candidates that passed vetting, from strongest to weakest. Without a `run_id`, it shows those from all runs. Candidates you rejected with `review` drop off the list. If the queue is empty, it prints `no candidates`. Each column (`severity`, `period_d`, `rp_rearth`, `score`, `failed`, `epoch_spike_frac`, `shared_signal_role`...) is explained in section 4 of the guide. `p_rank` is the model's probability (lesson A4): severity uses it only to **lower** priority, never to raise it. `p_abs` is the same value corrected for how rare planets are among new signals; it is for reading only. Only signals that passed the deterministic vetting with a score of at least 0.8 can reach P1 or P0; a failed signal with a high `p_rank` stays at P2 at most.

### `dossier`

```powershell
uv run planethunter dossier <signal_id>
```

Generates the HTML dossier for a signal and prints its path, in the format `data/dossiers/tic<TIC>_sig<signal_id>.html`. Open it in your browser. How to read each section: guide, section 4, and [lesson M5](../intermediate/m5-vetting-in-practice.md).

### `alert`

```powershell
uv run planethunter alert 20261009T204130Z-single-s69
uv run planethunter alert 20261009T204130Z-single-s69 --send
```

Generates the dossier for each candidate and prepares the message for those that are P0 or P1. **Without `--send`, nothing leaves your computer**: the messages go to `data/outbox/YYYY-MM-DD.md`. With `--send`, they go to Telegram or Discord, if configured (see below).

Before sending (and also in the simulation), the command runs the crossmatch again for each P0 and P1 against freshly loaded mirrors, and skips the signal if: a mirror is missing or stale; the class is no longer `NEW`; or the same target, with the same period, was already alerted in the last 30 days. P2 never generates an immediate alert. Each printed line gives the signal, the channel and the result, such as `signal 1071: outbox dry_run`.

### `review`

```powershell
uv run planethunter review <signal_id> rejected --reason systematic --note "absent in sectors 67, 68 and 97"
uv run planethunter review <signal_id> follow_up --note "no other sectors; wait for new data"
uv run planethunter review <signal_id> approved
```

Records your decision. The status is `approved`, `rejected` or `follow_up`. Rejecting requires `--reason`: `eb` (eclipsing binary), `blend` (contamination from a neighbor), `systematic` (instrumental defect), `noise`, `already_known` or `other`. `--note` is free text. The command confirms with a line such as `signal 1234: rejected [systematic] absent in sectors 67, 68 and 97`. Your decisions become training examples for a future classifier (lesson A4).

### `run-target`

```powershell
uv run planethunter run-target 261136679
uv run planethunter run-target 100100827 --sectors 69
uv run planethunter run-target 261136679 --skip-ingest
```

Does the ingestion, a search that stitches together all of the star's sectors on disk, the crossmatch and the basic vetting, and generates a dossier for each signal with SDE ≥ 9. It prints the `run_id`, a table with each signal (`signal_id`, period, `t0_btjd`, depth, duration, `sde`, `snr`, `n_transits`, crossmatch class, matched object, vetting verdict and score) and the path of each dossier, in lines like:

```text
dossier for signal 1234: data/dossiers/tic261136679_sig1234.html
```

If no signal clears the minimum SDE, the table is replaced by `no signal above the minimum SDE`. `--sectors` limits the ingestion (sectors downloaded earlier still go into the search); `--skip-ingest` uses only what is already on disk. Deep vetting does not run here. If you see `` WARNING: mirrors missing or stale; run `planethunter mirrors sync`. ``, run `mirrors sync`.

Good for studying stars with known planets, such as Pi Mensae (TIC 261136679, [lesson B5](../basic/b5-human-eye-practice.md)) and WASP-18 (TIC 100100827, [lesson P3](../programming/p3-lightkurve-in-practice.md)).

### `run-sector`

```powershell
uv run planethunter run-sector 69 --limit 200
```

Everything end to end: syncs the mirrors if any of them is about to expire, downloads, searches, runs the crossmatch, basic vetting, deep vetting of the candidates, dossiers and alerts. Options: `--limit`, `--skip-ingest` and `--send` (without it, alerts only go to `data/outbox/`).

### `benchmark build` and `benchmark run`

```powershell
uv run planethunter benchmark build 69
uv run planethunter benchmark run 69
```

`build` downloads the ExoFOP TOI list and freezes the sector's TOIs with an SNR of at least `--min-snr` (default 10) and a period up to 13 days, in `data/benchmark/sector_0069.csv`. With `--kind fp`, it freezes the TFOPWG false positives. `run` downloads these targets, searches them and measures **recall**: how many of the known TOIs the system finds again. Options: `--workers`, `--skip-ingest` and `--run <run_id>` (evaluates an existing run). The report goes to `docs/benchmarks/` and the details to `data/benchmark/result_<run_id>.csv`. In sector 69, the measured recall was 91.1 % (123 of 135 detectable TOIs).

Use the benchmark before and after any change to `config/thresholds.yaml` (lesson A5).

## Walkthrough: my first sector

Let us run sector 69 with only 200 stars, step by step. It takes a few minutes.

```powershell
uv run planethunter mirrors sync
uv run planethunter mirrors status                 # all "ok"?
uv run planethunter ingest sector 69 --limit 200   # downloads 200 light curves
uv run planethunter search --sector 69             # write down the run_id
uv run planethunter crossmatch <run_id>
uv run planethunter vet <run_id>
uv run planethunter candidates <run_id>
uv run planethunter dossier <signal_id>            # for each candidate you want to see
uv run planethunter alert <run_id>                 # simulation in data/outbox/
```

Replace `<run_id>` and `<signal_id>` with the values printed. Careful: `search --sector 69` searches all the sector 69 light curves already on disk, not just the last 200.

If you prefer, the shortcut is `uv run planethunter run-sector 69 --limit 200`. But do the step-by-step version at least once: you get to see what each stage produces.

**What to expect.** Many signals, almost all `NEW` or `KNOWN_*`, and maybe no candidates. That is the most common result. In the project's first real slice, 2,164 stars from sector 69 gave 887 signals, 648 `NEW`, 11 approved by basic vetting and, after deep vetting, **0 P1** and 3 P2. Each stage removes what does not hold up.

!!! tip "In the tool"
    All the commands on this page are in `src/planethunter/cli.py`. Each one is only a few lines long and calls functions from `src/planethunter/pipeline.py`. After [lesson P1](../programming/p1-python-basics.md), open the file and look for, say, `def run_target`: you will see the same ingestion, search and crossmatch sequence described above.

## Where the files live

| Path | Contents |
|---|---|
| `data/parquet/` | Light curves, one per star and sector (about 0.5 MB each) |
| `data/mirrors/` | Copies of the catalogs, each with a `.json` file recording the rows, the checksum and the version |
| `data/planethunter.duckdb` | Database with signals, crossmatch, vetting, candidates and alerts |
| `data/dossiers/` | HTML dossiers |
| `data/outbox/` | Simulated alerts, one file per day |
| `data/cache/` | Pixels, Gaia and FPP downloaded by `vet-deep` |
| `data/models/` | The calibrated model (`vetting_lr.json`) written by `calibrate` |
| `data/benchmark/` | Frozen lists and benchmark results |
| `config/thresholds.yaml` | Every limit, each with the reason why |

The `data/` folder does not go into Git. A full sector has about 20,000 stars; for the 2,164 in the test, the Parquet files took up about 1 GB. To keep the data on another disk, set the `PLANETHUNTER_DATA` variable before running the commands: `$env:PLANETHUNTER_DATA = "D:\planethunter-data"`. It applies to that terminal.

To read the Parquet files and the database in Python, see [lesson P3](../programming/p3-lightkurve-in-practice.md).

## Telegram alerts

1. In Telegram, chat with **@BotFather**, send `/newbot` and follow the instructions. It gives you back a **token**, a password for your bot.
2. Send any message to your new bot.
3. In your browser, open `https://api.telegram.org/bot<TOKEN>/getUpdates`, replacing `<TOKEN>` with yours. Look for `"chat":{"id":` and write down the number: it is your **chat id**.
4. In VS Code, create a file at the root of the project named exactly `.env`:

```text
TG_TOKEN=123456:ABC-your-token
TG_CHAT_ID=123456789
```

For Discord, add `DISCORD_WEBHOOK=` with the address of the channel's webhook. Then run `alert` or `run-sector` with `--send`. Only P0 or P1 candidates generate a message.

The same `.env` file can hold `PLANETHUNTER_MAX_WORKERS=4` to cap the CPU cores (see `search`). One setting per line, with no comments on the same line.

## Precautions

!!! warning "The `.env` file is secret"
    Whoever has the token controls your bot. `.env` is already in `.gitignore`. Check with `git check-ignore .env`: if it prints `.env`, it is protected. Never copy it anywhere else or show it in a screenshot. If it leaks, generate a new token with @BotFather using `/revoke`.

- **Never announce a discovery.** P1 means the signal survived the automatic tests, not that it is a planet. The path is: signal, candidate, CTOI, TOI, validated planet, confirmed planet. The last steps require other telescopes (guide, section 7).
- **Do not change limits without measuring.** Any change to `config/thresholds.yaml` requires running the benchmark before and after.
- **One command at a time.** Two commands writing to the database at the same time cause a "lock" error.
- **Be gentle with the servers.** Start with `--limit` and do not raise `--workers` without a reason.

## Exercises

!!! example "Exercise 1. Stale mirror"
    `mirrors status` shows `toi STALE <48 h age= 52.3 h`. What happens if you run `search`, `crossmatch` and `alert` now? How do you fix it?

    ??? success "Show answer"
        The search runs normally, because it does not use the mirrors. In the crossmatch, every signal that would be `NEW` becomes `UNVERIFIED`: with an outdated TOI list, there is no way to guarantee it is new. No alert goes out, and `alert` reports the signal as skipped because of `stale mirrors`. The fix: `uv run planethunter mirrors sync` and then `crossmatch <run_id>` again. `run-sector` does this by itself when any mirror is less than 6 hours from expiring.

!!! example "Exercise 2. From run to alert"
    You ran `search --sector 70` and got a `run_id`. Write the sequence of commands up to having the deep vetting and a simulated alert.

    ??? success "Show answer"
        ```powershell
        uv run planethunter crossmatch <run_id>
        uv run planethunter vet <run_id>
        uv run planethunter vet-deep <run_id>
        uv run planethunter candidates <run_id>
        uv run planethunter alert <run_id>
        ```
        The order matters: `vet` uses the crossmatch class to decide who becomes a candidate, and `vet-deep` only looks at the candidates `vet` created. Without `--send`, the alert stays in `data/outbox/`.

!!! example "Exercise 3. Recording a rejection"
    A P2 has `rp_rearth` 25, `depth_ppm` 30,000 and `failed` equal to `odd_even`. In the dossier, the odd transits are much deeper than the even ones. Record your decision.

    ??? success "Show answer"
        ```powershell
        uv run planethunter review <signal_id> rejected --reason eb --note "odd/even differ, Rp 25"
        ```
        Alternating depths point to an eclipsing binary with twice the period (lesson B4), and 25 R⊕ is too big for a planet. The `eb` reason helps the future classifier learn this pattern.

## Lab checklist

- [ ] I installed with `uv sync` and `tools/fpp`, and the tests passed
- [ ] I synced the mirrors and read `mirrors status`
- [ ] I ran `run-target` on Pi Mensae and on WASP-18
- [ ] I did the "my first sector" walkthrough with `--limit 200`
- [ ] I opened a dossier and a file in `data/outbox/`
- [ ] I recorded at least one review with `review`
- [ ] I checked that `.env` is ignored by Git

## Going further

- The project's beginner's guide (`docs/BEGINNERS_GUIDE.md`, in the repository), sections 3 and 4. Explains each step and how to read each column and plot.
- ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/)). A page for each star, with TOIs, CTOIs and community notes; it is where you check a candidate before any decision.
- NASA's TESS page at HEASARC ([heasarc.gsfc.nasa.gov](https://heasarc.gsfc.nasa.gov/docs/tess/)). Explains the sectors, cameras and cadences of the light curves that `ingest` downloads.
