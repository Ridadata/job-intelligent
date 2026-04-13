"""Silver → Gold enrichment pipeline.

Generates Sentence-BERT embeddings, classifies seniority, normalizes
titles, classifies taxonomy category, validates via Pydantic,
computes demand scores, and applies job_cleaner Gold standardization
for the Gold layer (dw_job_offers).
"""

import logging
from typing import Any

from etl.db import get_supabase_client
from etl.embeddings import generate_embeddings_batch
from etl.monitoring import track_pipeline
from etl.nlp import extract_skills
from etl.skill_normalization import normalize_skills
from etl.taxonomy import classify_job
from etl.validation import validate_gold_row
from pipeline.cleaning.job_cleaner import (
    build_gold_record,
    is_valid_job,
    IngestionMetrics,
)

logger = logging.getLogger(__name__)


def enrich_to_gold(model: str = "all-MiniLM-L6-v2", batch_size: int = 50) -> int:
    """Enrich Silver offers with embeddings and metadata for Gold layer.

    Reads job_offers without a corresponding dw_job_offers row, generates
    Sentence-BERT embeddings, classifies seniority and taxonomy, normalizes
    titles and skills, validates via Pydantic, and upserts into dw_job_offers.

    Args:
        model: Sentence-BERT model name for embedding generation.
        batch_size: Number of offers to process per batch.

    Returns:
        Total number of rows enriched.
    """
    client = get_supabase_client()
    total_enriched = 0
    total_read = 0
    total_skipped = 0
    total_errors = 0
    total_quarantined = 0
    metrics = IngestionMetrics("gold_enrichment")

    with track_pipeline("enrich", metadata={"model": model, "batch_size": batch_size}) as run:
        while True:
            # Fetch Silver offers that are NOT yet in Gold
            result = _fetch_unenriched_offers(client, batch_size)

            if not result.data:
                break

            offers = result.data
            total_read += len(offers)
            metrics.fetched += len(offers)

            # Pre-filter: reject invalid jobs to quarantine
            valid_offers = []
            for offer in offers:
                if is_valid_job(offer):
                    valid_offers.append(offer)
                else:
                    total_quarantined += 1
                    metrics.rejected += 1
                    logger.warning(
                        "QUARANTINED offer %s — failed validation: %s",
                        offer["id"], offer.get("title", "")[:80],
                    )

            if not valid_offers:
                logger.info("Batch had 0 valid offers after filtering — skipping")
                continue

            # Log sample offers for debugging
            for sample in valid_offers[:2]:
                logger.info(
                    "SAMPLE offer: id=%s title=%r company=%r",
                    sample["id"], sample.get("title", "")[:60], sample.get("company", "")[:40],
                )

            # Build text for embedding: title + description + skills
            texts = []
            for offer in valid_offers:
                skills_str = " ".join(offer.get("required_skills", []) or [])
                text = f"{offer.get('title', '')} {offer.get('description', '')[:500]} {skills_str}"
                texts.append(text.strip())

            # Generate embeddings in batch
            try:
                embeddings = generate_embeddings_batch(texts, model_name=model)
            except Exception:
                logger.error("Embedding generation failed for batch of %d", len(texts), exc_info=True)
                total_errors += len(valid_offers)
                continue

            # Build Gold rows
            gold_rows: list[dict[str, Any]] = []
            for offer, embedding in zip(valid_offers, embeddings):
                try:
                    combined_text = f"{offer.get('title', '')} {offer.get('description', '')}"

                    # Apply job_cleaner Gold standardization
                    gold_std = build_gold_record(offer)

                    row = {
                        "offer_id": offer["id"],
                        "embedding": embedding,
                        "normalized_title": gold_std["clean_title"],
                        "seniority_level": gold_std["seniority_level"],
                        "tech_stack": normalize_skills(extract_skills(combined_text)),
                        "demand_score": _compute_demand_score(offer),
                        "category": classify_job(
                            offer.get("title", ""),
                            offer.get("description", ""),
                        ),
                        "contract_type_standardized": gold_std["contract_type_standardized"],
                        "dedup_key": gold_std["dedup_key"],
                    }

                    is_valid, validated = validate_gold_row(row)
                    if is_valid:
                        gold_rows.append(validated)
                    else:
                        total_skipped += 1
                        logger.warning(
                            "Gold validation failed for offer %s: %s",
                            offer["id"], validated,
                        )
                except Exception:
                    total_errors += 1
                    logger.error(
                        "Failed to build Gold row for offer %s",
                        offer.get("id", "?"), exc_info=True,
                    )

            # Upsert into Gold table
            if gold_rows:
                try:
                    client.table("dw_job_offers").upsert(
                        gold_rows, on_conflict="offer_id"
                    ).execute()
                    total_enriched += len(gold_rows)
                    metrics.cleaned += len(gold_rows)
                    metrics.inserted += len(gold_rows)
                    logger.info("Enriched batch of %d offers to Gold", len(gold_rows))
                except Exception:
                    total_errors += len(gold_rows)
                    logger.error(
                        "Failed to upsert Gold batch (%d rows)",
                        len(gold_rows), exc_info=True,
                    )
            else:
                logger.info("No valid Gold rows in this batch — skipping upsert")

        run.rows_in = total_read
        run.rows_out = total_enriched
        run.rows_skipped = total_skipped
        run.rows_error = total_errors

    metrics.log_summary()
    logger.info(
        "Gold enrichment complete: %d/%d rows (skipped=%d, quarantined=%d, errors=%d)",
        total_enriched, total_read, total_skipped, total_quarantined, total_errors,
    )
    return total_enriched


def _fetch_unenriched_offers(client: Any, batch_size: int) -> Any:
    """Fetch Silver offers without Gold rows using left join logic.

    This is a fallback when the get_unenriched_offers RPC is not available.
    Queries job_offers and filters out those already in dw_job_offers.

    Args:
        client: Supabase client.
        batch_size: Maximum rows to return.

    Returns:
        Query result with offer data.
    """
    # Get IDs already in Gold
    gold_result = (
        client.table("dw_job_offers")
        .select("offer_id")
        .execute()
    )
    existing_ids = {row["offer_id"] for row in (gold_result.data or [])}

    # Fetch Silver offers
    silver_result = (
        client.table("job_offers")
        .select("id, title, company, description, required_skills, published_at, source_id")
        .limit(batch_size + len(existing_ids))
        .execute()
    )

    if not silver_result.data:
        return silver_result

    # Filter out already-enriched offers
    filtered = [
        row for row in silver_result.data if row["id"] not in existing_ids
    ][:batch_size]

    silver_result.data = filtered
    return silver_result


def _compute_demand_score(offer: dict[str, Any]) -> float:
    """Compute a demand score for a job offer.

    Based on recency and number of skills requested.
    Score ranges from 0.0 to 1.0.

    Args:
        offer: An offer dict with published_at, required_skills, etc.

    Returns:
        A float between 0.0 and 1.0.
    """
    score = 0.5  # baseline

    # Boost for more skills (more specific = higher demand signal)
    skills = offer.get("required_skills") or []
    if len(skills) >= 5:
        score += 0.2
    elif len(skills) >= 3:
        score += 0.1

    # Boost for recent publication
    if offer.get("published_at"):
        score += 0.2

    # Boost for having salary info (indicates serious listing)
    if offer.get("salary_min") or offer.get("salary_max"):
        score += 0.1

    return min(score, 1.0)
