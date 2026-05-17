"""
migrate_data.py — Copy data from Supabase cloud to local PostgreSQL via REST API.

This script bypasses the pg_dump/DNS IPv6 issue entirely by using the
Supabase PostgREST API (HTTPS) to read data and psycopg2 to write locally.

Usage:
    python scripts/migrate_data.py [--tables TABLE1,TABLE2] [--batch 500]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

# ── resolve project root and load .env ───────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

def _load_env(path: Path) -> None:
    """Read .env file and set variables that are not already set."""
    if not path.exists():
        return
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env(ENV_FILE)

# ── now safe to import third-party ───────────────────────────────────────────
try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extras import Json as PgJson
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

# ── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("migrate_data")

# ── configuration ─────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

LOCAL_DB_HOST = os.environ.get("LOCAL_DB_HOST", "localhost")
LOCAL_DB_PORT = int(os.environ.get("LOCAL_DB_PORT", "5432"))
LOCAL_DB_USER = os.environ.get("LOCAL_DB_USER", "postgres")
LOCAL_DB_PASSWORD = os.environ.get("LOCAL_DB_PASSWORD", "postgres")
LOCAL_DB_NAME = os.environ.get("LOCAL_DB_NAME", "job_intelligent")

# Tables in dependency order (parents before children)
DEFAULT_TABLES = [
    "sources",
    "raw_job_offers",
    "job_offers",
    "dw_job_offers",
    "users",
    "candidate_profiles",
    "cv_documents",
    "saved_jobs",
    "applications",
    "recommendation_history",
    "pipeline_runs",
    "candidates",          # legacy table kept for compatibility
    "recommendations",     # legacy table kept for compatibility
    "scraping_logs",       # legacy table kept for compatibility
]

# Tables to skip entirely (they may not exist in Supabase or have RLS blocking)
SKIP_TABLES: set[str] = set()


# ── schema introspection ──────────────────────────────────────────────────────

def get_column_types(
    conn: "psycopg2.extensions.connection",
    table: str,
) -> dict[str, tuple[str, str]]:
    """Return {column_name: (data_type, udt_name)} for a table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return {row[0]: (row[1], row[2]) for row in cur.fetchall()}


def adapt_value(val: Any, data_type: str, udt_name: str) -> Any:
    """
    Convert a value received from Supabase REST API to the correct Python type
    for psycopg2 so PostgreSQL accepts it without a type-cast error.
    """
    if val is None:
        return None
    if data_type == "ARRAY":
        # REST API may return a Python list or a JSON-encoded string
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                pass
        # psycopg2 serialises Python lists as PostgreSQL array literals natively
        return val
    if udt_name == "vector":
        # vector columns: Supabase returns a JSON list of floats or a string
        if isinstance(val, list):
            return f"[{','.join(str(x) for x in val)}]"
        if isinstance(val, str) and val.startswith("["):
            return val  # already correct format
        return val
    if data_type in ("json", "jsonb"):
        if isinstance(val, (dict, list)):
            return PgJson(val)
        if isinstance(val, str):
            try:
                return PgJson(json.loads(val))
            except Exception:
                return val
        return val
    # dict/list not caught above — serialize as JSON string
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return val


# ── Supabase REST client ──────────────────────────────────────────────────────

def fetch_table(
    client: httpx.Client,
    table: str,
    batch_size: int = 500,
) -> list[dict[str, Any]]:
    """Fetch all rows from a Supabase table using paginated requests."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json",
        "Prefer": "count=exact",
    }

    all_rows: list[dict[str, Any]] = []
    offset = 0

    while True:
        params = {
            "select": "*",
            "limit": str(batch_size),
            "offset": str(offset),
        }
        resp = client.get(url, params=params, headers=headers, timeout=60)

        if resp.status_code == 404:
            log.warning("  Table %s not found in Supabase (404) — skipping", table)
            return []
        if resp.status_code == 401:
            log.warning("  Table %s access denied (401) — skipping", table)
            return []
        if resp.status_code not in (200, 206):
            log.warning(
                "  Table %s returned HTTP %s — skipping. Body: %s",
                table, resp.status_code, resp.text[:200],
            )
            return []

        rows: list[dict] = resp.json()
        if not rows:
            break
        all_rows.extend(rows)
        log.info("    fetched %d rows (total so far: %d)", len(rows), len(all_rows))

        if len(rows) < batch_size:
            break
        offset += batch_size
        time.sleep(0.1)  # be polite to Supabase rate limits

    return all_rows


# ── local PostgreSQL writer ───────────────────────────────────────────────────

def upsert_rows(
    conn: "psycopg2.extensions.connection",
    table: str,
    rows: list[dict[str, Any]],
    col_types: dict[str, tuple[str, str]] | None = None,
) -> int:
    """
    Insert rows into a local table using ON CONFLICT DO NOTHING.
    Returns number of rows inserted.
    """
    if not rows:
        return 0

    col_types = col_types or {}
    columns = list(rows[0].keys())
    col_str = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("%s" for _ in columns)
    sql = (
        f'INSERT INTO public."{table}" ({col_str}) '
        f"VALUES ({placeholders}) "
        f"ON CONFLICT DO NOTHING"
    )

    inserted = 0
    with conn.cursor() as cur:
        for row in rows:
            values = []
            for col in columns:
                dt, udt = col_types.get(col, ("text", "text"))
                values.append(adapt_value(row[col], dt, udt))
            try:
                cur.execute(sql, values)
                inserted += cur.rowcount
            except Exception as exc:  # noqa: BLE001
                log.debug("    row insert failed: %s", exc)
                conn.rollback()
                break
        conn.commit()

    return inserted


def truncate_and_insert(
    conn: "psycopg2.extensions.connection",
    table: str,
    rows: list[dict[str, Any]],
    batch_size: int = 500,
    col_types: dict[str, tuple[str, str]] | None = None,
) -> int:
    """Truncate table and bulk-insert all rows. Much faster than upsert_rows for full sync."""
    if not rows:
        return 0

    col_types = col_types or {}
    columns = list(rows[0].keys())
    col_str = ", ".join(f'"{c}"' for c in columns)
    sql = f'INSERT INTO public."{table}" ({col_str}) VALUES %s'

    total_inserted = 0
    with conn.cursor() as cur:
        try:
            cur.execute(f'TRUNCATE TABLE public."{table}" RESTART IDENTITY CASCADE')
            for start in range(0, len(rows), batch_size):
                batch = rows[start : start + batch_size]
                values = []
                for row in batch:
                    record = []
                    for col in columns:
                        dt, udt = col_types.get(col, ("text", "text"))
                        record.append(adapt_value(row[col], dt, udt))
                    values.append(tuple(record))
                psycopg2.extras.execute_values(cur, sql, values, template=None, page_size=batch_size)
                total_inserted += len(batch)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            log.error("  TRUNCATE+INSERT failed for %s: %s", table, exc)
            log.info("  Falling back to per-row upsert for %s", table)
            return upsert_rows(conn, table, rows, col_types=col_types)

    return total_inserted


# ── main ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate Supabase data to local PostgreSQL")
    parser.add_argument(
        "--tables",
        help="Comma-separated list of tables to migrate (default: all)",
        default="",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=500,
        help="Rows per API page request (default: 500)",
    )
    parser.add_argument(
        "--no-truncate",
        action="store_true",
        help="Use UPSERT instead of TRUNCATE+INSERT (slower but safer)",
    )
    args = parser.parse_args(argv)

    # Validate config
    if not SUPABASE_URL:
        log.error("SUPABASE_URL is not set. Check your .env file.")
        return 1
    if not SUPABASE_KEY:
        log.error("SUPABASE_KEY is not set. Check your .env file.")
        return 1

    tables = [t.strip() for t in args.tables.split(",") if t.strip()] if args.tables else DEFAULT_TABLES
    tables = [t for t in tables if t not in SKIP_TABLES]

    log.info("Supabase URL : %s", SUPABASE_URL)
    log.info("Local DB     : %s@%s:%d/%s", LOCAL_DB_USER, LOCAL_DB_HOST, LOCAL_DB_PORT, LOCAL_DB_NAME)
    log.info("Tables       : %s", tables)
    log.info("")

    # Connect to local PostgreSQL
    try:
        conn = psycopg2.connect(
            host=LOCAL_DB_HOST,
            port=LOCAL_DB_PORT,
            user=LOCAL_DB_USER,
            password=LOCAL_DB_PASSWORD,
            dbname=LOCAL_DB_NAME,
        )
        conn.autocommit = False
        log.info("Connected to local PostgreSQL.")
    except Exception as exc:
        log.error("Cannot connect to local PostgreSQL: %s", exc)
        return 1

    summary: list[tuple[str, int, int]] = []  # (table, fetched, inserted)

    with httpx.Client(follow_redirects=True) as client:
        for table in tables:
            log.info("──────────────────────────────────")
            log.info("Table: %s", table)

            log.info("  Fetching from Supabase …")
            rows = fetch_table(client, table, batch_size=args.batch)
            fetched = len(rows)
            log.info("  → %d rows fetched", fetched)

            if fetched == 0:
                summary.append((table, 0, 0))
                continue

            log.info("  Writing to local DB …")
            col_types = get_column_types(conn, table)
            if args.no_truncate:
                inserted = upsert_rows(conn, table, rows, col_types=col_types)
            else:
                inserted = truncate_and_insert(conn, table, rows, batch_size=args.batch, col_types=col_types)
            log.info("  → %d rows inserted/updated", inserted)
            summary.append((table, fetched, inserted))

    conn.close()

    # Print summary table
    log.info("")
    log.info("═══════════════════════════════════════════════════════════")
    log.info("%-30s  %8s  %8s", "TABLE", "FETCHED", "INSERTED")
    log.info("───────────────────────────────────────────────────────────")
    total_fetched = total_inserted = 0
    for tbl, f, i in summary:
        log.info("%-30s  %8d  %8d", tbl, f, i)
        total_fetched += f
        total_inserted += i
    log.info("───────────────────────────────────────────────────────────")
    log.info("%-30s  %8d  %8d", "TOTAL", total_fetched, total_inserted)
    log.info("═══════════════════════════════════════════════════════════")
    log.info("Migration complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
