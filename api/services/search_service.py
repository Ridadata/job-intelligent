"""Semantic search service — query → embedding → pgvector similarity search."""

import logging
import time
from typing import Any

from api.repositories.job_repository import JobRepository
from api.services.redis_service import get_cached, set_cached
from ai_services.embedding.generator import generate_embedding

logger = logging.getLogger(__name__)


async def semantic_search(
    job_repo: JobRepository,
    query: str,
    top_n: int = 20,
    min_score: float = 0.30,
    filter_contract: str | None = None,
    filter_location: str | None = None,
) -> dict[str, Any]:
    """Perform semantic search over job offers using embeddings.

    Converts the user's free-text query to an embedding, then searches
    the Gold layer via pgvector cosine similarity.

    Args:
        job_repo: JobRepository instance.
        query: Free-text search query.
        top_n: Maximum number of results.
        min_score: Minimum similarity threshold.
        filter_contract: Optional contract type filter.
        filter_location: Optional location filter.

    Returns:
        Dict with items (list of matches), total, query, and latency_ms.
    """
    start_time = time.time()

    # Check cache
    import hashlib
    cache_key = f"search:{hashlib.sha256(query.lower().encode()).hexdigest()[:16]}"
    cached = await get_cached(cache_key)
    if cached:
        latency = int((time.time() - start_time) * 1000)
        cached["latency_ms"] = latency
        return cached

    # Generate embedding from query text
    try:
        query_embedding = generate_embedding(query)
    except Exception as exc:
        logger.error("[SEARCH] Embedding generation failed: %s", exc, exc_info=True)
        return {"items": [], "total": 0, "query": query, "latency_ms": int((time.time() - start_time) * 1000)}

    # Similarity search via repository
    try:
        raw_matches = job_repo.match_by_embedding(
            query_embedding=query_embedding,
            match_threshold=min_score,
            match_count=top_n,
            filter_contract=filter_contract,
            filter_location=filter_location,
        )
    except Exception as exc:
        logger.error("[SEARCH] pgvector search failed: %s", exc, exc_info=True)
        raw_matches = []

    logger.info("[SEARCH] query='%s' | raw_matches=%d", query, len(raw_matches))

    items = []
    for match in raw_matches:
        items.append({
            "id": str(match["offer_id"]),
            "title": match.get("title"),
            "company": match.get("company"),
            "location": match.get("location"),
            "contract_type": match.get("contract_type"),
            "similarity_score": round(match.get("similarity", 0), 4),
            "tech_stack": match.get("tech_stack") or [],
        })

    latency_ms = int((time.time() - start_time) * 1000)

    result = {
        "items": items,
        "total": len(items),
        "query": query,
        "latency_ms": latency_ms,
    }

    # Cache for 5 minutes
    await set_cached(cache_key, result, ttl=300)

    logger.info(
        "Semantic search '%s' returned %d results in %dms",
        query, len(items), latency_ms,
    )

    return result
