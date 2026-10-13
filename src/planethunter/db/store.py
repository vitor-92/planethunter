"""DuckDB access. Only the main process writes (DuckDB allows one writer per file)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

SCHEMA = Path(__file__).with_name("schema.sql")

# Columns added after the initial creation. CREATE TABLE IF NOT EXISTS does not add them
# to older databases; these migrations run on every connection and are idempotent.
MIGRATIONS = [
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS edge_transit_fraction DOUBLE",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS detrend_window_days DOUBLE",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS alias_factor INTEGER",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS transit_times_json VARCHAR",
    "ALTER TABLE crossmatch ADD COLUMN IF NOT EXISTS match_type VARCHAR",
    "ALTER TABLE crossmatch ADD COLUMN IF NOT EXISTS host_eb BOOLEAN",
    "ALTER TABLE vetting ADD COLUMN IF NOT EXISTS fpp DOUBLE",
    "ALTER TABLE vetting ADD COLUMN IF NOT EXISTS nfpp DOUBLE",
    "ALTER TABLE vetting ADD COLUMN IF NOT EXISTS p_planet DOUBLE",
    # 2026-10-10 code audit (docs/PLAN.md §17)
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS duration_raw_hours DOUBLE",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS snr_pink DOUBLE",
    "ALTER TABLE signals ADD COLUMN IF NOT EXISTS detrend_windows_json VARCHAR",
    "ALTER TABLE crossmatch ADD COLUMN IF NOT EXISTS phase_checked BOOLEAN",
    "ALTER TABLE crossmatch ADD COLUMN IF NOT EXISTS epoch_spike_frac DOUBLE",
    "ALTER TABLE crossmatch ADD COLUMN IF NOT EXISTS shared_signal_tic BIGINT",
    "ALTER TABLE crossmatch ADD COLUMN IF NOT EXISTS shared_signal_sep_arcsec DOUBLE",
    "ALTER TABLE crossmatch ADD COLUMN IF NOT EXISTS shared_signal_role VARCHAR",
    "ALTER TABLE vetting ADD COLUMN IF NOT EXISTS p_abs DOUBLE",
    "ALTER TABLE vetting ADD COLUMN IF NOT EXISTS model_version VARCHAR",
]


def connect(root: Path, *, read_only: bool = False, retries: int = 30) -> duckdb.DuckDBPyConnection:
    """Open the database. read_only does not apply the schema and tolerates another process
    writing (retries while the file is locked by a writer)."""
    import time

    if read_only:
        for attempt in range(retries):
            try:
                return duckdb.connect(str(root / "planethunter.duckdb"), read_only=True)
            except duckdb.IOException:
                if attempt == retries - 1:
                    raise
                time.sleep(1.0)
    con = duckdb.connect(str(root / "planethunter.duckdb"))
    con.execute(SCHEMA.read_text(encoding="utf-8"))
    for stmt in MIGRATIONS:
        con.execute(stmt)
    return con


def upsert_df(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> int:
    """INSERT OR REPLACE by primary key. The df columns must exist in the table."""
    if df.empty:
        return 0
    cols = ", ".join(df.columns)
    con.register("_upsert", df)
    try:
        con.execute(f"INSERT OR REPLACE INTO {table} ({cols}) SELECT {cols} FROM _upsert")
    finally:
        con.unregister("_upsert")
    return len(df)


def insert_df(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    cols = ", ".join(df.columns)
    con.register("_insert", df)
    try:
        con.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM _insert")
    finally:
        con.unregister("_insert")
    return len(df)
