"""Recommendation router — POST /api/v1/recommendations, GET /api/v1/candidates/{id}/skill-gap."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_current_user, get_db
from api.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
)
from api.repositories.candidate_repository import CandidateRepository
from api.repositories.job_repository import JobRepository
from api.services.recommendation_service import get_recommendations
from api.services.skill_gap_service import get_skill_gap

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["recommendations"])


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get job recommendations for a candidate",
    description=(
        "Generates personalized job recommendations using multi-signal "
        "matching: skill overlap, embedding similarity, seniority alignment, "
        "and location preference. Returns ranked results with explanations."
    ),
)
async def recommendations(
    request: RecommendationRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> RecommendationResponse:
    """Generate job recommendations for a candidate.

    Args:
        request: Recommendation request with candidate_id, top_n, filters.
        user: Authenticated user from JWT.
        db: Supabase client dependency.

    Returns:
        RecommendationResponse with matched jobs, metadata, and latency.
    """
    try:
        return await get_recommendations(
            candidate_repo=CandidateRepository(db),
            job_repo=JobRepository(db),
            candidate_id=request.candidate_id,
            top_n=request.top_n,
            min_score=request.min_score,
            filters=request.filters,
        )
    except ValueError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc
    except Exception as exc:
        logger.error("Recommendation endpoint error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal error generating recommendations",
        ) from exc


@router.get(
    "/candidates/{candidate_id}/skill-gap",
    summary="Get skill gap analysis for a candidate",
    description=(
        "Analyzes the candidate's skills against similar job offers "
        "to identify the most in-demand skills they are missing."
    ),
)
async def skill_gap(
    candidate_id: UUID,
    top_n: int = Query(10, ge=1, le=50, description="Top missing skills to return"),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> dict:
    """Get skill gap analysis for a candidate.

    Args:
        candidate_id: UUID of the candidate.
        top_n: Number of top missing skills.
        user: Authenticated user from JWT.
        db: Supabase client dependency.

    Returns:
        Skill gap report with missing skills and frequencies.
    """
    try:
        return await get_skill_gap(
            candidate_repo=CandidateRepository(db),
            job_repo=JobRepository(db),
            candidate_id=candidate_id,
            top_n_skills=top_n,
        )
    except Exception as exc:
        logger.error("Skill gap endpoint error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal error during skill gap analysis",
        ) from exc
