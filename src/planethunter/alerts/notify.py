"""Alert delivery. The gate is re-evaluated at send time; nothing is lost on failure.

Send-time gate (CLAUDE.md invariant, audit A1): right before sending (and in dry-run), every
P0/P1 is re-classified with `crossmatch.batch.classify_frame` against freshly loaded mirrors.
Nothing is sent if any mirror is missing or stale for its freshness policy, or if the fresh
class is no longer NEW (e.g. the host got a TOI after the batch crossmatch); the crossmatch
row is updated with the fresh result and checked_at (UTC).

Channels via environment variables (or a .env file at the repo root, never committed):
  TG_TOKEN, TG_CHAT_ID      -> Telegram
  DISCORD_WEBHOOK           -> Discord
With no channel configured, or with dry_run, the message goes to <data>/outbox/YYYY-MM-DD.md.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from planethunter.catalogs.mirrors import load_known
from planethunter.config import REPO_ROOT, Config
from planethunter.crossmatch.core import MatchClass
from planethunter.db.store import connect, insert_df
from planethunter.log import get_logger

log = get_logger(__name__)
IMMEDIATE = ("P0", "P1")
DEDUP_DAYS = 30


def load_env(path: Path = REPO_ROOT / ".env") -> None:
    """Load KEY=VALUE from .env without overriding the environment. Values are never logged."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


@dataclass
class Outcome:
    signal_id: int
    channel: str
    status: str  # sent | dry_run | failed | skipped
    reason: str = ""


def mirrors_line(ages: dict, cfg: Config, now: datetime | None = None) -> str:
    """Which databases were queried and the sync date of the oldest live mirror (rule 3)."""
    now = now or datetime.now(UTC)
    names = sorted(getattr(k, "value", k) for k in ages)
    live = [
        a
        for k, a in ages.items()
        if a is not None and cfg.crossmatch.max_age_hours(getattr(k, "value", k)) is not None
    ]
    oldest = (now - timedelta(hours=max(live))).strftime("%Y-%m-%d %H:%M UTC") if live else "?"
    return f"{len(names)} catalogs ({', '.join(names)}); oldest live mirror synced {oldest}"


def format_message(r: pd.Series, mirror_info: str) -> str:
    rp = r.get("rp_rearth")
    rp_s = f"{rp:.1f} R⊕" if pd.notna(rp) else "R* unknown"
    tmag = f"{r['tmag']:.2f}" if pd.notna(r.get("tmag")) else "?"
    return (
        f"[{r['severity']}] Candidate TIC {int(r['tic_id'])}  Tmag {tmag}\n"
        f"P = {r['period_days']:.5f} d   Rp = {rp_s}   depth = {r['depth_ppm']:.0f} ppm   "
        f"SDE {r['sde']:.1f}  SNR {r['snr']:.1f}\n"
        f"Basic vetting {r['score']:.2f}; deep vetting pending. Sectors {r['sectors']}. "
        f"Known host: {'yes' if r['host_known'] else 'no'}\n"
        f"Crossmatch NEW, re-checked at send time against {mirror_info}\n"
        f"Dossier: {r['dossier_path'] or '(not generated)'}"
    )


def _send_telegram(text: str) -> None:
    from planethunter.net import session

    tok, chat = os.environ["TG_TOKEN"], os.environ["TG_CHAT_ID"]
    resp = session().post(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        json={"chat_id": chat, "text": text},
        timeout=15,
    )
    resp.raise_for_status()


def _send_discord(text: str) -> None:
    from planethunter.net import session

    resp = session().post(os.environ["DISCORD_WEBHOOK"], json={"content": text}, timeout=15)
    resp.raise_for_status()


def channels() -> dict[str, object]:
    load_env()
    out: dict[str, object] = {}
    if os.environ.get("TG_TOKEN") and os.environ.get("TG_CHAT_ID"):
        out["telegram"] = _send_telegram
    if os.environ.get("DISCORD_WEBHOOK"):
        out["discord"] = _send_discord
    return out


def _already_alerted(con, tic_id: int, period: float) -> bool:
    rows = con.execute(
        f"""
        SELECT s.period_days FROM alerts a JOIN signals s USING (signal_id)
        WHERE s.tic_id = ? AND a.status IN ('sent', 'dry_run')
          AND a.created_at > now() - INTERVAL {DEDUP_DAYS} DAY
        """,
        [tic_id],
    ).fetchall()
    return any(abs(p / period - 1) < 0.01 for (p,) in rows)


RECHECK_COLUMNS = (
    "match_class",
    "host_known",
    "matched_name",
    "matched_source",
    "alias",
    "phase_consistent",
    "phase_checked",
    "match_type",
    "host_eb",
    "separation_arcsec",
    "n_host_objects",
    "n_nearby_objects",
    "notes",
    "mirror_ages_json",
    "checked_at",
)


def recheck_crossmatch(
    con, signal_ids: list[int], known: pd.DataFrame, ages: dict, cfg: Config
) -> dict[int, str]:
    """Re-classify signals against the given (fresh) mirrors and update their crossmatch rows.

    Only the per-signal columns are refreshed; run-level flags (epoch spikes, shared
    signals) keep their batch values. Returns {signal_id: fresh match_class}.
    """
    from planethunter.crossmatch.batch import classify_frame
    from planethunter.pipeline import CROSSMATCH_SIGNALS_SQL

    if not signal_ids:
        return {}
    ids = ",".join(str(int(x)) for x in signal_ids)
    sigs = con.execute(CROSSMATCH_SIGNALS_SQL + f" WHERE s.signal_id IN ({ids})").df()
    if sigs.empty:
        return {}
    fresh = classify_frame(sigs, known, ages, cfg.crossmatch)
    fresh["mirror_ages_json"] = json.dumps({getattr(k, "value", k): v for k, v in ages.items()})
    fresh["checked_at"] = datetime.now(UTC).replace(tzinfo=None)
    sets = ", ".join(f"{c} = ?" for c in RECHECK_COLUMNS)
    for row in fresh.to_dict("records"):
        vals = [None if _isna(row[c]) else row[c] for c in RECHECK_COLUMNS]
        con.execute(f"UPDATE crossmatch SET {sets} WHERE signal_id = ?", [*vals, row["signal_id"]])
    return dict(zip(fresh["signal_id"].astype(int), fresh["match_class"], strict=True))


def _isna(x: object) -> bool:
    try:
        return bool(pd.isna(x))
    except (TypeError, ValueError):
        return False


def send_alerts(
    root: Path, cfg: Config, run_id: str | None = None, *, dry_run: bool = True
) -> list[Outcome]:
    """Alert P0/P1 candidates not yet alerted. P2 is left for the digest.

    Each P0/P1 is re-classified right now against freshly loaded mirrors; it is skipped if a
    mirror is missing/stale or the fresh class is not NEW.
    """
    known, ages = load_known(root)
    stale = cfg.crossmatch.stale_sources(ages)
    from planethunter.pipeline import candidate_table

    cands = candidate_table(root, run_id)
    con = connect(root)
    extra = con.execute(
        "SELECT signal_id, s.period_days, s.t0_btjd, v.fit_depth_ppm AS depth_ppm, "
        "k.dossier_path, c.match_class FROM candidates k JOIN signals s USING (signal_id) "
        "JOIN vetting v USING (signal_id) JOIN crossmatch c USING (signal_id)"
    ).df()
    cands = cands.drop(columns=[c for c in ("depth_ppm",) if c in cands]).merge(
        extra, on="signal_id", how="left", suffixes=("", "_x")
    )
    outcomes: list[Outcome] = []
    chans = {} if dry_run else channels()
    mirror_info = mirrors_line(ages, cfg)
    outbox_lines: list[str] = []
    rows = []
    immediate = cands[cands["severity"].isin(IMMEDIATE)]
    fresh: dict[int, str] = {}
    if not stale and len(immediate):
        fresh = recheck_crossmatch(con, [int(x) for x in immediate["signal_id"]], known, ages, cfg)
    for _, r in immediate.iterrows():
        sid = int(r["signal_id"])
        if stale:
            outcomes.append(Outcome(sid, "-", "skipped", f"stale mirrors: {stale}"))
            continue
        cls = fresh.get(sid)
        if cls != MatchClass.NEW.value:
            reason = f"class is now {cls} at the send-time re-check" if cls else "re-check failed"
            outcomes.append(Outcome(sid, "-", "skipped", reason))
            log.warning(
                "alert blocked by re-check", extra={"tic_id": int(r["tic_id"]), "error": reason}
            )
            continue
        if _already_alerted(con, int(r["tic_id"]), float(r["period_days"])):
            outcomes.append(Outcome(sid, "-", "skipped", "already alerted in the last 30 days"))
            continue
        msg = format_message(r, mirror_info)
        if not chans:
            outbox_lines.append(msg)
            rows.append(
                {
                    "signal_id": sid,
                    "channel": "outbox",
                    "severity": r["severity"],
                    "status": "dry_run",
                    "message": msg,
                    "error": None,
                }
            )
            outcomes.append(Outcome(sid, "outbox", "dry_run"))
            continue
        for name, fn in chans.items():
            try:
                fn(msg)
                rows.append(
                    {
                        "signal_id": sid,
                        "channel": name,
                        "severity": r["severity"],
                        "status": "sent",
                        "message": msg,
                        "error": None,
                    }
                )
                outcomes.append(Outcome(sid, name, "sent"))
            except Exception as exc:  # never lose an alert: stays 'failed' for resending
                rows.append(
                    {
                        "signal_id": sid,
                        "channel": name,
                        "severity": r["severity"],
                        "status": "failed",
                        "message": msg,
                        "error": type(exc).__name__,
                    }
                )
                outcomes.append(Outcome(sid, name, "failed", type(exc).__name__))
                log.error("send failed", extra={"tic_id": int(r["tic_id"]), "error": name})
    if rows:
        insert_df(con, "alerts", pd.DataFrame(rows))
    con.close()
    if outbox_lines:
        box = root / "outbox" / f"{datetime.now(UTC):%Y-%m-%d}.md"
        box.parent.mkdir(parents=True, exist_ok=True)
        with box.open("a", encoding="utf-8") as fh:
            for m in outbox_lines:
                fh.write(m + "\n\n---\n\n")
    return outcomes
