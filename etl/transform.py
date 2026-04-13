"""Bronze → Silver transformation pipeline.

Reads unprocessed raw_job_offers, cleans and normalizes the data,
extracts skills via NLP, validates with Pydantic, normalizes skills
against canonical dictionary, and writes to the job_offers Silver table.
"""

import logging
import re
import time
from typing import Any

from etl.db import get_supabase_client
from etl.monitoring import track_pipeline
from etl.nlp import extract_skills, normalize_contract_type
from etl.skill_normalization import normalize_skills
from etl.taxonomy import classify_job
from etl.validation import validate_silver_row

logger = logging.getLogger(__name__)

# ── Data-domain filter ────────────────────────────────────────────────────────
# Keywords that indicate a data / AI / analytics job.  Matched case-insensitively
# against title first; if no hit the description is checked as a fallback.
_DATA_KEYWORDS: list[str] = [
    # Roles
    r"data\s*scientist", r"data\s*engineer", r"data\s*analyst",
    r"data\s*architect", r"data\s*manager", r"data\s*steward",
    r"data\s*quality", r"data\s*governance",
    r"machine\s*learning", r"deep\s*learning",
    r"ml\s*engineer", r"mlops",
    r"intelligence\s*artificielle", r"artificial\s*intelligence",
    r"\bIA\b", r"\bAI\b",
    r"big\s*data", r"data\s*lake", r"data\s*warehouse",
    r"business\s*intelligence", r"\bBI\b",
    r"analytics\s*engineer", r"data\s*ops",
    r"NLP", r"computer\s*vision",
    # Titles containing "data" as a standalone word (not "database admin" alone)
    r"\bdata\b",
    # Tech stack strongly associated with data roles
    r"\bETL\b", r"\bELT\b", r"\bdbt\b",
    r"\bspark\b", r"\bhadoop\b", r"\bhive\b", r"\bkafka\b",
    r"\bairflow\b", r"\bdatabricks\b", r"\bsnowflake\b",
    r"\btensorflow\b", r"\bpytorch\b", r"\bscikit.learn\b",
    r"\bpower\s*bi\b", r"\btableau\b", r"\blooker\b",
    r"\bpandas\b",
]
_DATA_RE = re.compile("|".join(_DATA_KEYWORDS), re.IGNORECASE)


def _is_data_job(title: str, description: str) -> bool:
    """Return True if the offer belongs to the data / AI domain."""
    if _DATA_RE.search(title):
        return True
    # Fall back to description (first 2000 chars to stay fast)
    if description and _DATA_RE.search(description[:2000]):
        return True
    return False


def transform_to_silver(batch_size: int = 100) -> int:
    """Transform unprocessed Bronze rows into Silver (job_offers).

    Reads raw_job_offers where processed=false in batches, extracts
    structured fields from raw_json, runs NLP skill extraction,
    normalizes skills against canonical dictionary, validates via
    Pydantic, and inserts into job_offers.

    Args:
        batch_size: Number of raw rows to process per batch.

    Returns:
        Total number of rows transformed.
    """
    client = get_supabase_client()
    total_transformed = 0
    total_read = 0
    total_skipped = 0
    total_errors = 0

    with track_pipeline("transform", metadata={"batch_size": batch_size}) as run:
        while True:
            # Fetch a batch of unprocessed raw offers
            result = (
                client.table("raw_job_offers")
                .select("id, source_id, raw_json")
                .eq("processed", False)
                .limit(batch_size)
                .execute()
            )

            if not result.data:
                break

            rows = result.data
            total_read += len(rows)
            silver_rows: list[dict[str, Any]] = []
            raw_ids: list[str] = []

            for row in rows:
                try:
                    silver = _extract_silver_fields(row)
                    raw_ids.append(row["id"])  # always mark processed, data or not
                    if silver:
                        # Validate via Pydantic before insert
                        is_valid, validated = validate_silver_row(silver)
                        if is_valid:
                            silver_rows.append(validated)
                        else:
                            total_skipped += 1
                            logger.warning(
                                "Silver validation failed for raw offer %s: %s",
                                row["id"], str(validated)[:200],
                            )
                    else:
                        total_skipped += 1
                except Exception:
                    logger.error(
                        "Failed to transform raw offer %s", row["id"], exc_info=True
                    )
                    raw_ids.append(row["id"])  # still mark processed to avoid infinite retry
                    total_errors += 1
                    continue

            if silver_rows:
                # Log sample for debugging
                for sample in silver_rows[:2]:
                    logger.info(
                        "SAMPLE Silver: title=%r company=%r contract=%s skills=%d",
                        sample.get("title", "")[:60],
                        sample.get("company", "")[:40],
                        sample.get("contract_type", "?"),
                        len(sample.get("required_skills", [])),
                    )

                # Insert into Silver table
                try:
                    client.table("job_offers").insert(silver_rows).execute()
                except Exception:
                    logger.error(
                        "Failed to insert Silver batch (%d rows) — continuing",
                        len(silver_rows), exc_info=True,
                    )
                    total_errors += len(silver_rows)
                    silver_rows = []  # don't count as transformed
            else:
                logger.info("Batch had 0 Silver rows after filtering (read=%d, skipped=%d)", len(rows), total_skipped)

            if raw_ids:
                # Mark raw rows as processed
                try:
                    client.table("raw_job_offers").update(
                        {"processed": True}
                    ).in_("id", raw_ids).execute()
                except Exception:
                    logger.error("Failed to mark raw rows as processed", exc_info=True)

            total_transformed += len(silver_rows)
            logger.info(
                "Batch complete: read=%d, transformed=%d, skipped=%d, errors=%d",
                len(rows), len(silver_rows), total_skipped, total_errors,
            )

        run.rows_in = total_read
        run.rows_out = total_transformed
        run.rows_skipped = total_skipped
        run.rows_error = total_errors

    logger.info(
        "Silver transformation complete: %d/%d rows (skipped=%d, errors=%d)",
        total_transformed, total_read, total_skipped, total_errors,
    )
    return total_transformed


def _extract_silver_fields(row: dict[str, Any]) -> dict[str, Any] | None:
    """Extract and normalize Silver-layer fields from a raw offer.

    Handles different raw_json structures from different sources.

    Args:
        row: A raw_job_offers row with id, source_id, and raw_json.

    Returns:
        A dict ready for insertion into job_offers, or None if invalid.
    """
    raw = row.get("raw_json", {})
    if not raw:
        return None

    title = raw.get("title", "").strip()
    if not title:
        logger.warning("Skipping raw offer %s: missing title", row["id"])
        return None

    # Silver layer: keep only data-domain jobs
    if not _is_data_job(title, raw.get("description", "")):
        logger.debug("Skipping non-data offer %s: %s", row["id"], title[:80])
        return None

    description = raw.get("description", "")
    combined_text = f"{title} {description}"

    # Extract salary range
    salary_min, salary_max = _parse_salary(raw)

    return {
        "source_id": row["source_id"],
        "raw_offer_id": row["id"],
        "title": title,
        "company": raw.get("company", "").strip() or None,
        "location": raw.get("location", "").strip() or None,
        "contract_type": normalize_contract_type(raw.get("contract_type", "")),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "required_skills": normalize_skills(extract_skills(combined_text)),
        "description": description[:10000] if description else None,
        "published_at": raw.get("published_at") or raw.get("date") or None,
    }


def _parse_salary(raw: dict[str, Any]) -> tuple[float | None, float | None]:
    """Parse salary information from raw offer data.

    Handles various formats: explicit min/max, single value, range string.

    Args:
        raw: The raw_json dictionary.

    Returns:
        Tuple of (salary_min, salary_max) as floats, or (None, None).
    """
    salary_min = raw.get("salary_min")
    salary_max = raw.get("salary_max")

    # Try parsing from a combined salary field
    if salary_min is None and salary_max is None:
        salary_raw = raw.get("salary", "")
        if salary_raw and isinstance(salary_raw, str):
            import re

            numbers = re.findall(r"[\d]+(?:[.,]\d+)?", salary_raw.replace(" ", ""))
            numbers = [float(n.replace(",", ".")) for n in numbers]
            if len(numbers) >= 2:
                salary_min, salary_max = min(numbers), max(numbers)
            elif len(numbers) == 1:
                salary_min = salary_max = numbers[0]

    # Validate
    try:
        salary_min = float(salary_min) if salary_min is not None else None
        salary_max = float(salary_max) if salary_max is not None else None
    except (ValueError, TypeError):
        salary_min = salary_max = None

    return salary_min, salary_max
