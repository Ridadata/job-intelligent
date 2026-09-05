"""Export the latest Job Intelligent analytical datasets from Supabase.

This exporter is aligned with the current platform schema (candidate_profiles,
recommendation_history, pipeline_runs, etc.) and avoids legacy tables that are
no longer the source of truth for Power BI.

Typical usage:
    python powerbi/export_to_csv.py --clean

Incremental usage (where supported by updated_at columns):
    python powerbi/export_to_csv.py --since 2026-01-01T00:00:00Z
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from supabase import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatasetSpec:
    """Configuration for one exported dataset.

    Attributes:
        name: Supabase table or view name.
        select_clause: Columns to select.
        page_size: Fetch page size.
        order_by: Optional sort column.
        updated_at_column: Optional timestamp column for --since filtering.
    """

    name: str
    select_clause: str
    page_size: int
    order_by: str | None = None
    updated_at_column: str | None = None


# Materialized views and current source-of-truth tables for analytics.
LATEST_DATASETS: list[DatasetSpec] = [
    DatasetSpec("mv_offers_by_skill", "skill_name,offer_count,week_date", 2000, "week_date"),
    DatasetSpec(
        "mv_salary_by_role",
        "job_title,contract_type,salary_avg,salary_min,salary_max,offer_count",
        2000,
        "salary_avg",
    ),
    DatasetSpec("mv_offers_by_location", "city,offer_count,avg_salary", 2000, "offer_count"),
    DatasetSpec("mv_market_trends", "source_name,week_date,offer_count", 2000, "week_date"),
    DatasetSpec(
        "mv_top_companies",
        "company_name,active_offers,avg_salary,contract_types",
        1000,
        "active_offers",
    ),
    DatasetSpec(
        "sources",
        "id,name,base_url,last_scraped_at",
        1000,
        "name",
        "last_scraped_at",
    ),
    DatasetSpec(
        "job_offers",
        "id,source_id,title,company,location,contract_type,salary_min,salary_max,required_skills,published_at,created_at,updated_at",
        2000,
        "published_at",
        "updated_at",
    ),
    DatasetSpec(
        "dw_job_offers",
        "id,offer_id,normalized_title,seniority_level,tech_stack,demand_score,category,contract_type_standardized,dedup_key,created_at",
        2000,
        "created_at",
        "created_at",
    ),
    DatasetSpec(
        "candidate_profiles",
        "id,user_id,title,skills,experience_years,education_level,location,salary_expectation,preferred_contract_types,profile_completeness,created_at,updated_at",
        2000,
        "updated_at",
        "updated_at",
    ),
    DatasetSpec(
        "cv_documents",
        "id,candidate_id,file_type,parsed_skills,parsed_experience,parsed_education,parsing_status,parsed_at,created_at",
        2000,
        "created_at",
        "created_at",
    ),
    DatasetSpec(
        "saved_jobs",
        "id,candidate_id,job_offer_id,saved_at",
        2000,
        "saved_at",
        "saved_at",
    ),
    DatasetSpec(
        "recommendation_history",
        "id,candidate_id,job_offer_id,similarity_score,score_breakdown,action,created_at",
        3000,
        "created_at",
        "created_at",
    ),
    DatasetSpec(
        "pipeline_runs",
        "id,stage,status,source_name,rows_in,rows_out,rows_skipped,rows_error,duration_ms,error_message,started_at,finished_at,created_at",
        3000,
        "started_at",
        "started_at",
    ),
]


def _build_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed CLI namespace.
    """

    parser = argparse.ArgumentParser(
        description="Export latest Supabase datasets for Power BI (schema-aligned)."
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent / "exports"),
        help="Directory where CSV files will be generated.",
    )
    parser.add_argument(
        "--since",
        default=None,
        help=(
            "Optional ISO timestamp (e.g. 2026-01-01T00:00:00Z). "
            "Applies only to datasets that expose an updated timestamp column."
        ),
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing CSV files in the output directory before export.",
    )
    return parser.parse_args()


def _validate_env() -> None:
    """Validate required environment variables.

    Raises:
        SystemExit: If SUPABASE_URL or SUPABASE_KEY is missing.
    """

    missing = [k for k in ("SUPABASE_URL", "SUPABASE_KEY") if not os.environ.get(k)]
    if missing:
        logger.error("Missing environment variables: %s", ", ".join(missing))
        raise SystemExit(1)


def _create_supabase_client() -> "Client":
    """Create Supabase client from environment variables.

    Returns:
        Initialized Supabase client.
    """

    try:
        from supabase import create_client
    except ModuleNotFoundError as exc:
        logger.error(
            "Missing Python dependency 'supabase'. Install project requirements first: pip install -r requirements.txt"
        )
        raise SystemExit(3) from exc

    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def _parse_since(since: str | None) -> datetime | None:
    """Parse optional ISO timestamp.

    Args:
        since: Timestamp string from CLI.

    Returns:
        Parsed datetime in UTC, or None.

    Raises:
        SystemExit: If format is invalid.
    """

    if not since:
        return None
    try:
        dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
    except ValueError as exc:
        logger.error("Invalid --since value '%s': %s", since, exc)
        raise SystemExit(2) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _serialize_cell(value: Any) -> Any:
    """Convert complex values to CSV-safe representations.

    Args:
        value: Cell value from Supabase row.

    Returns:
        Scalar value or serialized string.
    """

    if value is None:
        return ""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            return ";".join(str(item) for item in value)
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return value


def _fetch_dataset(
    client: "Client",
    dataset: DatasetSpec,
    since_utc: datetime | None,
) -> list[dict[str, Any]]:
    """Fetch rows for one dataset with pagination.

    Args:
        client: Supabase client.
        dataset: Dataset export spec.
        since_utc: Optional UTC timestamp for incremental fetch.

    Returns:
        List of rows.
    """

    rows: list[dict[str, Any]] = []
    offset = 0

    while True:
        query = client.table(dataset.name).select(dataset.select_clause)

        if since_utc and dataset.updated_at_column:
            query = query.gte(dataset.updated_at_column, since_utc.isoformat())

        if dataset.order_by:
            query = query.order(dataset.order_by, desc=True)

        response = query.range(offset, offset + dataset.page_size - 1).execute()
        batch = response.data or []
        rows.extend(batch)

        logger.info(
            "  %s: fetched %d rows (total %d)",
            dataset.name,
            len(batch),
            len(rows),
        )

        if len(batch) < dataset.page_size:
            break
        offset += dataset.page_size

    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write rows to CSV.

    Args:
        path: Target CSV file path.
        rows: Rows to write.
    """

    if not rows:
        path.write_text("no_data\n", encoding="utf-8")
        return

    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _serialize_cell(v) for k, v in row.items()})


def _clean_output_dir(output_dir: Path) -> None:
    """Remove existing CSV and manifest files.

    Args:
        output_dir: Output directory.
    """

    for file_path in output_dir.glob("*.csv"):
        file_path.unlink(missing_ok=True)
    manifest = output_dir / "_export_manifest.json"
    manifest.unlink(missing_ok=True)


def _write_manifest(
    output_dir: Path,
    generated_at: datetime,
    since_utc: datetime | None,
    summary: list[tuple[str, int, str]],
) -> None:
    """Write export metadata manifest.

    Args:
        output_dir: Export directory.
        generated_at: Export generation timestamp.
        since_utc: Optional incremental cursor.
        summary: Per-dataset summary tuples.
    """

    manifest = {
        "generated_at": generated_at.isoformat(),
        "since": since_utc.isoformat() if since_utc else None,
        "dataset_count": len(summary),
        "datasets": [
            {"name": name, "rows": rows, "status": status}
            for name, rows, status in summary
        ],
    }
    (output_dir / "_export_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _print_summary(output_dir: Path, generated_at: datetime, summary: list[tuple[str, int, str]]) -> None:
    """Print export summary to stdout.

    Args:
        output_dir: Export directory.
        generated_at: Timestamp.
        summary: Per-dataset summary tuples.
    """

    print("\n" + "=" * 76)
    print(f"Export complete at {generated_at.isoformat()}")
    print(f"Output folder: {output_dir.resolve()}")
    print("=" * 76)
    print(f"{'Dataset':<34} {'Rows':>10}  Status")
    print("-" * 76)
    for name, count, status in summary:
        print(f"{name:<34} {count:>10}  {status}")
    print("=" * 76)


def main() -> None:
    """Run CSV export for the latest Power BI-aligned dataset list."""

    args = _build_args()
    _validate_env()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    since_utc = _parse_since(args.since)

    if args.clean:
        _clean_output_dir(output_dir)

    client = _create_supabase_client()
    generated_at = datetime.now(timezone.utc)
    summary: list[tuple[str, int, str]] = []

    for dataset in LATEST_DATASETS:
        logger.info("Exporting %s", dataset.name)
        try:
            rows = _fetch_dataset(client, dataset, since_utc)
            csv_path = output_dir / f"{dataset.name}.csv"
            _write_csv(csv_path, rows)
            summary.append((dataset.name, len(rows), "ok"))
            logger.info("  saved %s (%d rows)", csv_path.name, len(rows))
        except Exception as exc:
            summary.append((dataset.name, 0, f"failed: {exc}"))
            logger.error("  failed exporting %s: %s", dataset.name, exc)

    _write_manifest(output_dir, generated_at, since_utc, summary)
    _print_summary(output_dir, generated_at, summary)


if __name__ == "__main__":
    main()
