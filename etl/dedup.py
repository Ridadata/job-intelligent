"""Cross-source deduplication for the Silver layer.

Detects and marks duplicate job offers that come from different sources
but represent the same position, using content-based hash keys and
fuzzy title+company similarity as a fallback.
"""

import logging
import re
from typing import Any

from etl.db import get_supabase_client
from pipeline.cleaning.job_cleaner import compute_dedup_key

logger = logging.getLogger(__name__)

# ── Similarity thresholds ────────────────────────────────────────────────────
_TITLE_SIMILARITY_THRESHOLD = 0.85
_COMPANY_SIMILARITY_THRESHOLD = 0.80


def _normalize_text(text: str) -> str:
    """Lowercase, strip, and collapse whitespace for comparison.

    Args:
        text: Raw text string.

    Returns:
        Normalized text.
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    # Remove common suffixes that vary across sources
    text = re.sub(r"\s*[-–|(].*$", "", text)
    return text


def _jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two strings (word-level).

    Args:
        a: First string.
        b: Second string.

    Returns:
        Float between 0.0 and 1.0.
    """
    if not a or not b:
        return 0.0
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def find_duplicates(batch_size: int = 500) -> list[dict[str, Any]]:
    """Find potential duplicate pairs in the Silver table.

    Groups offers by normalized location, then checks title + company
    similarity within each group. Only compares offers from different sources.

    Args:
        batch_size: Max offers to scan per location group.

    Returns:
        List of duplicate pair dicts: {offer_a_id, offer_b_id, similarity, reason}.
    """
    client = get_supabase_client()
    duplicates: list[dict[str, Any]] = []

    # Get distinct locations to group by
    result = (
        client.table("job_offers")
        .select("location")
        .limit(1000)
        .execute()
    )
    locations = {r["location"] for r in (result.data or []) if r.get("location")}

    for location in locations:
        offers_result = (
            client.table("job_offers")
            .select("id, source_id, title, company")
            .eq("location", location)
            .limit(batch_size)
            .execute()
        )
        offers = offers_result.data or []

        # Compare pairs from different sources
        for i, a in enumerate(offers):
            for b in offers[i + 1:]:
                if a["source_id"] == b["source_id"]:
                    continue

                title_sim = _jaccard_similarity(
                    _normalize_text(a.get("title", "")),
                    _normalize_text(b.get("title", "")),
                )
                company_sim = _jaccard_similarity(
                    _normalize_text(a.get("company", "")),
                    _normalize_text(b.get("company", "")),
                )

                if (title_sim >= _TITLE_SIMILARITY_THRESHOLD
                        and company_sim >= _COMPANY_SIMILARITY_THRESHOLD):
                    duplicates.append({
                        "offer_a_id": a["id"],
                        "offer_b_id": b["id"],
                        "title_similarity": round(title_sim, 3),
                        "company_similarity": round(company_sim, 3),
                        "reason": "fuzzy_match",
                    })

    logger.info("Dedup scan found %d potential duplicate pairs", len(duplicates))
    return duplicates


def find_hash_duplicates(batch_size: int = 1000) -> list[dict[str, Any]]:
    """Find duplicates using content-based hash(title + company + location).

    Faster than fuzzy matching. Use this as the primary dedup strategy
    and fall back to find_duplicates() for near-matches.

    Args:
        batch_size: Max offers to scan.

    Returns:
        List of duplicate group dicts with dedup_key and offer IDs.
    """
    client = get_supabase_client()

    result = (
        client.table("job_offers")
        .select("id, title, company, location, source_id, created_at")
        .limit(batch_size)
        .execute()
    )
    offers = result.data or []

    # Group by dedup key
    key_groups: dict[str, list[dict[str, Any]]] = {}
    for offer in offers:
        key = compute_dedup_key(
            offer.get("title", ""),
            offer.get("company", ""),
            offer.get("location", ""),
        )
        key_groups.setdefault(key, []).append(offer)

    duplicates: list[dict[str, Any]] = []
    for key, group in key_groups.items():
        if len(group) > 1:
            # Sort by created_at, keep the earliest
            group.sort(key=lambda x: x.get("created_at", ""))
            duplicates.append({
                "dedup_key": key,
                "canonical_id": group[0]["id"],
                "duplicate_ids": [o["id"] for o in group[1:]],
                "count": len(group),
            })

    logger.info(
        "Hash dedup scan: %d duplicate groups across %d offers",
        len(duplicates), len(offers),
    )
    return duplicates


def deduplicate_silver(dry_run: bool = True) -> dict[str, Any]:
    """Find and optionally remove duplicate Silver offers.

    The offer with the earlier created_at is kept (canonical). The newer
    duplicates are removed from the Silver table.

    Args:
        dry_run: If True, only report duplicates without deleting.

    Returns:
        Summary dict with counts and duplicate IDs.
    """
    duplicates = find_duplicates()

    if not duplicates:
        return {"duplicates_found": 0, "removed": 0}

    # Collect IDs to remove (keep the first seen / earlier one)
    client = get_supabase_client()
    ids_to_remove: set[str] = set()

    for pair in duplicates:
        a_result = (
            client.table("job_offers")
            .select("id, created_at")
            .eq("id", pair["offer_a_id"])
            .limit(1)
            .execute()
        )
        b_result = (
            client.table("job_offers")
            .select("id, created_at")
            .eq("id", pair["offer_b_id"])
            .limit(1)
            .execute()
        )

        if a_result.data and b_result.data:
            a_date = a_result.data[0].get("created_at", "")
            b_date = b_result.data[0].get("created_at", "")
            # Keep the earlier one, mark the later one for removal
            remove_id = pair["offer_b_id"] if a_date <= b_date else pair["offer_a_id"]
            ids_to_remove.add(remove_id)

    removed = 0
    if not dry_run and ids_to_remove:
        for offer_id in ids_to_remove:
            try:
                client.table("job_offers").delete().eq("id", offer_id).execute()
                removed += 1
            except Exception:
                logger.error("Failed to delete duplicate offer %s", offer_id, exc_info=True)

    result = {
        "duplicates_found": len(duplicates),
        "ids_to_remove": list(ids_to_remove),
        "removed": removed,
        "dry_run": dry_run,
    }
    logger.info("Dedup result: %s", result)
    return result
