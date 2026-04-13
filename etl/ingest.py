"""Raw data ingestion into the Bronze layer (raw_job_offers)."""

import logging
import time
from typing import Any

from etl.db import get_supabase_client
from etl.monitoring import track_pipeline

logger = logging.getLogger(__name__)


def _get_source_id(source_name: str) -> str:
    """Look up the source UUID by name, creating it if absent.

    Args:
        source_name: The source platform name (e.g., 'indeed').

    Returns:
        The UUID string of the source.
    """
    client = get_supabase_client()
    result = (
        client.table("sources")
        .select("id")
        .eq("name", source_name)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]["id"]

    # Auto-create source
    insert_result = (
        client.table("sources")
        .upsert({"name": source_name, "base_url": f"https://{source_name}"}, on_conflict="name")
        .execute()
    )
    if insert_result.data:
        return insert_result.data[0]["id"]

    raise ValueError(f"Source '{source_name}' not found and could not be created")


def ingest_raw(offers: list[dict[str, Any]], source_name: str) -> int:
    """Ingest raw scraped offers into the Bronze layer.

    Upserts into raw_job_offers on (source_id, external_id) to avoid
    duplicates. Each offer dict must contain an 'external_id' key.
    Logs run metrics to pipeline_runs table.

    Args:
        offers: List of raw offer dictionaries. Each must have 'external_id'.
        source_name: Name of the source platform (e.g., 'indeed').

    Returns:
        Number of rows upserted.
    """
    if not offers:
        logger.warning("No offers to ingest for source '%s'", source_name)
        return 0

    start = time.time()
    client = get_supabase_client()
    source_id = _get_source_id(source_name)
    skipped = 0

    rows = []
    for offer in offers:
        external_id = offer.get("external_id")
        if not external_id:
            logger.warning("Skipping offer without external_id: %s", offer.get("title", "unknown"))
            skipped += 1
            continue

        rows.append({
            "source_id": source_id,
            "external_id": str(external_id),
            "raw_json": offer,
            "processed": False,
        })

    if not rows:
        logger.warning("No valid offers to ingest for source '%s'", source_name)
        return 0

    # Upsert in batches to avoid payload limits
    batch_size = 500
    total_upserted = 0

    with track_pipeline("ingest", source_name=source_name, metadata={"batch_size": batch_size}) as run:
        run.rows_in = len(offers)

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            try:
                result = (
                    client.table("raw_job_offers")
                    .upsert(batch, on_conflict="source_id,external_id")
                    .execute()
                )
                total_upserted += len(result.data) if result.data else 0
            except Exception:
                logger.error(
                    "Failed to upsert batch %d-%d for source '%s'",
                    i, i + len(batch), source_name, exc_info=True,
                )
                _log_scraping_run(source_id, "failed", 0, time.time() - start, str(batch))
                raise

        duration_ms = int((time.time() - start) * 1000)

        # Update last_scraped_at on the source
        client.table("sources").update(
            {"last_scraped_at": "now()"}
        ).eq("id", source_id).execute()

        # Log successful run
        _log_scraping_run(source_id, "success", total_upserted, duration_ms)

        run.rows_out = total_upserted
        run.rows_skipped = skipped

    logger.info(
        "Ingested %d raw offers from '%s' in %dms",
        total_upserted, source_name, duration_ms,
    )
    return total_upserted


def _log_scraping_run(
    source_id: str,
    status: str,
    rows_inserted: int,
    duration_ms: float,
    error_message: str | None = None,
) -> None:
    """Write a record to scraping_logs.

    Args:
        source_id: The source UUID.
        status: One of 'success', 'failed', 'partial'.
        rows_inserted: Number of rows inserted/upserted.
        duration_ms: Duration in milliseconds.
        error_message: Error details if status is 'failed'.
    """
    try:
        client = get_supabase_client()
        client.table("scraping_logs").insert({
            "source_id": source_id,
            "status": status,
            "rows_inserted": rows_inserted,
            "duration_ms": int(duration_ms),
            "error_message": error_message,
        }).execute()
    except Exception:
        logger.error("Failed to write scraping log", exc_info=True)
