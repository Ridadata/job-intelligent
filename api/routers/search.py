"""Search router — GET /api/v1/search — semantic job search."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_current_user, get_db
from api.repositories.job_repository import JobRepository
from api.services.search_service import semantic_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get(
    "/search",
    summary="Semantic job search",
    description=(
        "Converts a free-text query to an embedding and returns "
        "semantically similar job offers via pgvector."
    ),
)
async def search_jobs(
    q: str = Query(..., min_length=2, max_length=500, description="Search query"),
    top_n: int = Query(20, ge=1, le=100, description="Max results"),
    contract_type: str | None = Query(None, description="Filter by contract type"),
    location: str | None = Query(None, description="Filter by location"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> dict:
    """Perform semantic search over job offers.

    Args:
        q: Free-text search query.
        top_n: Max number of results.
        contract_type: Optional contract type filter.
        location: Optional location filter.
        user: Authenticated user from JWT.
        db: Supabase client dependency.

    Returns:
        Dict with items, total, query, and latency_ms.
    """
    try:
        return await semantic_search(
            job_repo=JobRepository(db),
            query=q,
            top_n=top_n,
            filter_contract=contract_type,
            filter_location=location,
        )
    except Exception as exc:
        logger.error("Semantic search failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal error during semantic search",
        ) from exc
