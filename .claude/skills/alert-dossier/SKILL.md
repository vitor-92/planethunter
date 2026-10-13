---
name: alert-dossier
description: Candidate dossier structure, P0/P1/P2 severity rules, deduplication, and integration with Telegram, Discord and e-mail. Use when implementing or changing notifications, dossiers or the human review queue.
---

# Alerts and dossier

## Gate before any alert

```
match_class == NEW
and mirrors.max_age_h < 48
and vetting.score >= 0.5
and not duplicate(tic_id, period, 30 days)
```
Re-evaluate the gate at send time, not only at classification.

## Severity

| Sev | Condition | Channel | When |
|---|---|---|---|
| P0 | NEW, score ≥ 0.8, FPP < 0.1 | Telegram + Discord + e-mail | immediate |
| P1 | NEW, 0.5 ≤ score < 0.8 | daily digest | 09:00 |
| P2 | KNOWN_TOI with improved period, ambiguous NEARBY_KNOWN | weekly digest | Monday |

## Short message (Telegram/Discord)

```
[P0] New candidate  TIC 123456789  Tmag 12.3
P = 14.2031 d   Rp = 2.6 R⊕   depth = 980 ppm   SDE 11.4  SNR 9.8
Vetting 0.86   FPP 0.04   NFPP 2e-4   Sectors 70, 97
Crossmatch: Archive ✗  TOI ✗  CTOI ✗  EBcat ✗  ADS ✗  (mirrors 2026-10-09)
Dossier: file:///.../dossiers/cand_000123.html
```
Vocabulary: "candidate", never "discovery".

## Telegram

```python
import os, requests

TOKEN, CHAT = os.environ["TG_TOKEN"], os.environ["TG_CHAT_ID"]
requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={"chat_id": CHAT, "text": msg},
    timeout=10,
)
with open(png, "rb") as fh:
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={"chat_id": CHAT},
        files={"photo": fh},
        timeout=30,
    )
```

## Discord

```python
requests.post(os.environ["DISCORD_WEBHOOK"], json={"content": msg}, timeout=10)
# attachment: files={"file": open(png, "rb")}
```

Delivery failure: write to `alerts` with `status=pending`, retry with backoff, never discard.

## HTML dossier (fixed order)

1. Header: TIC, coordinates, Tmag, Teff, R*, M*, sectors, class, severity, novelty score.
2. Raw and detrended light curve (all sectors), transits marked, momentum dumps marked.
3. Phase-fold with batman model; zoom ±2 durations.
4. Odd-even side by side; secondary window at phase 0.5.
5. River plot (one row per epoch).
6. TLS periodogram with annotated peaks.
7. Mean TPF image + difference image + overlaid Gaia sources + aperture.
8. Table of the 13 tests: value, threshold, verdict, note.
9. Crossmatch table: database, mirror date, method, result, link.
10. FPP/NFPP and triceratops scenarios.
11. Next action: submit CTOI (field checklist), request follow-up, discard.
12. Provenance: run_id, pipeline_version, light curve author, parameters.

Useful links: ExoFOP `https://exofop.ipac.caltech.edu/tess/target.php?id=<TIC>`, Archive `https://exoplanetarchive.ipac.caltech.edu/overview/TIC%20<TIC>`, SIMBAD `https://simbad.cds.unistra.fr/simbad/sim-coo?Coord=<ra>+<dec>&Radius=30&Radius.unit=arcsec`.

Plots with `matplotlib.use("Agg")`, 1200×600 px, PNG; HTML with Jinja2, self-contained (base64 images) so it opens offline.

## Review queue (Streamlit)

List by severity → embedded dossier → approve / reject / follow-up buttons + note. Writes `candidates.review_status`, `reviewed_at`, `reviewer`. Rejection asks for a reason from a fixed list (EB, blend, systematic, noise, already known, other) to feed the ML.

## CTOI (ExoFOP)

Usual fields: TIC, period and error, epoch (BJD) and error, depth (ppm), duration (h), notes, sectors, pipeline, plots. Generate the draft from the dossier; submission is manual and only after approval in the queue.

## State in the code (v1)

- Severity (`alerts/severity.py`): P0 = NEW, score ≥ 0.8, deep vetting complete and FPP < 0.1; P1 = NEW, score ≥ 0.8; P2 = the rest of the approved ones, EB host or star without a radius in the TIC.
- `planethunter alert [run] [--send]`: without `--send` writes to `data/outbox/`; with `--send` uses `.env` (`TG_TOKEN`, `TG_CHAT_ID`, `DISCORD_WEBHOOK`). Gate re-evaluated at send time; 30-day deduplication.
- Review: `planethunter review <signal_id> approved|rejected|follow_up [--reason eb|blend|systematic|noise|already_known|other] [--note ...]`. Rejected ones disappear from the default `candidates` list.
- Dossier: `alerts/dossier.py`, self-contained HTML in `data/dossiers/`, includes the difference image when it exists.
