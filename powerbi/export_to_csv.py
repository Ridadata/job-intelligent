"""
Export all Job Intelligent data from Supabase to CSV files for Power BI.

Usage:
    python powerbi/export_to_csv.py

Output: powerbi/exports/ folder with one CSV per table/view.
"""

import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
EXPORT_DIR = Path(__file__).parent / "exports"

# Tables/views to export — (name, page_size)
EXPORTS = [
    # Materialized views (pre-aggregated — use these for Power BI visuals)
    ("mv_offers_by_skill",    1000),
    ("mv_salary_by_role",     1000),
    ("mv_offers_by_location", 1000),
    ("mv_market_trends",      1000),
    ("mv_top_companies",      500),
    # Core tables
    ("job_offers",            2000),
    ("sources",               100),
    ("candidates",            500),
    ("recommendations",       1000),
    ("scraping_logs",         1000),
]


def _validate_env() -> None:
    """Raise if required environment variables are missing."""
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_KEY") if not os.environ.get(k)]
    if missing:
        logger.error("Missing environment variables: %s", ", ".join(missing))
        sys.exit(1)


def _fetch_all(client, table: str, page_size: int) -> list[dict]:
    """Fetch all rows from a table using pagination.

    Args:
        client: Supabase client instance.
        table: Table or view name.
        page_size: Number of rows per request.

    Returns:
        List of row dicts.
    """
    rows = []
    offset = 0
    while True:
        response = (
            client.table(table)
            .select("*")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = response.data or []
        rows.extend(batch)
        logger.info("  %s: fetched %d rows (total so far: %d)", table, len(batch), len(rows))
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write rows to a CSV file.

    Args:
        path: Output file path.
        rows: List of row dicts.
    """
    if not rows:
        logger.warning("  No data — writing empty CSV: %s", path.name)
        path.write_text("no_data\n")
        return

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Flatten list/array columns to semicolon-separated strings
            flat = {
                k: (";".join(str(x) for x in v) if isinstance(v, list) else v)
                for k, v in row.items()
            }
            writer.writerow(flat)


def main() -> None:
    """Export all tables and materialized views to CSV files."""
    _validate_env()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary = []
    for table, page_size in EXPORTS:
        logger.info("Exporting: %s", table)
        try:
            rows = _fetch_all(client, table, page_size)
            csv_path = EXPORT_DIR / f"{table}.csv"
            _write_csv(csv_path, rows)
            summary.append((table, len(rows), "✅ OK"))
            logger.info("  Saved → %s (%d rows)", csv_path.name, len(rows))
        except Exception as exc:
            summary.append((table, 0, f"❌ {exc}"))
            logger.error("  Failed to export %s: %s", table, exc)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Export complete — {timestamp}")
    print(f"Output folder: {EXPORT_DIR.resolve()}")
    print("=" * 60)
    print(f"{'Table/View':<30} {'Rows':>8}  Status")
    print("-" * 60)
    for table, count, status in summary:
        print(f"{table:<30} {count:>8}  {status}")
    print("=" * 60)
    print("\nNext step: open Power BI Desktop → Get Data → Text/CSV")
    print(f"and import files from:\n  {EXPORT_DIR.resolve()}")


if __name__ == "__main__":
    main()
