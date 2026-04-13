"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Models ───────────────────────────────────────────────────────────


class RecommendationFilters(BaseModel):
    """Optional filters for recommendation search.

    Attributes:
        contract_type: Filter by contract type (CDI, CDD, etc.).
        location: Filter by location (partial match).
    """

    contract_type: Optional[str] = None
    location: Optional[str] = None


class RecommendationRequest(BaseModel):
    """Request body for the recommendation endpoint.

    Attributes:
        candidate_id: UUID of the candidate to match.
        top_n: Maximum number of recommendations to return.
        min_score: Minimum similarity score threshold.
        filters: Optional search filters.
    """

    candidate_id: UUID
    top_n: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.20, ge=0.0, le=1.0)
    filters: Optional[RecommendationFilters] = None


# ── Response Models ──────────────────────────────────────────────────────────


class JobOfferMatch(BaseModel):
    """A single job offer match in recommendation results.

    Attributes:
        offer_id: UUID of the matched job offer.
        title: Job title.
        company: Company name.
        location: Job location.
        contract_type: Type of contract.
        similarity_score: Composite match score (0-1).
        matched_skills: Skills matching between candidate and offer.
        missing_skills: Job skills the candidate lacks.
        score_breakdown: Breakdown of composite score components.
        explanation_text: Human-readable match explanation.
        tech_stack: Technologies required for the offer.
    """

    model_config = {"populate_by_name": True}

    offer_id: UUID = Field(alias="job_id")
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    contract_type: Optional[str] = None
    similarity_score: float
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    score_breakdown: dict[str, float] = {}
    explanation_text: str = ""
    tech_stack: list[str] = []


class RecommendationMeta(BaseModel):
    """Metadata for recommendation response.

    Attributes:
        model: The embedding model used.
        threshold: The similarity threshold applied.
        cached: Whether results were served from cache.
    """

    model: str
    threshold: float
    cached: bool = False


class RecommendationResponse(BaseModel):
    """Response envelope for recommendations.

    Attributes:
        data: List of matched job offers.
        total: Total number of matches.
        latency_ms: Processing time in milliseconds.
        meta: Response metadata.
    """

    data: list[JobOfferMatch]
    total: int
    latency_ms: int
    meta: RecommendationMeta


class APIResponse(BaseModel):
    """Generic API response envelope.

    Attributes:
        data: Response payload (any type).
        error: Error message if request failed.
        meta: Additional metadata.
    """

    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class CandidateCreate(BaseModel):
    """Request body for creating a candidate profile.

    Attributes:
        email: Candidate email address.
        current_title: Current job title.
        skills: List of skills.
        years_experience: Years of professional experience.
        preferred_location: Preferred work location.
    """

    email: str
    current_title: Optional[str] = None
    skills: list[str] = []
    years_experience: Optional[int] = None
    preferred_location: Optional[str] = None


class CandidateResponse(BaseModel):
    """Response for candidate profile.

    Attributes:
        id: Candidate UUID.
        email: Candidate email.
        current_title: Current job title.
        skills: Skills list.
        years_experience: Years of experience.
        preferred_location: Preferred location.
        created_at: Profile creation timestamp.
    """

    id: UUID
    email: str
    current_title: Optional[str] = None
    skills: list[str] = []
    years_experience: Optional[int] = None
    preferred_location: Optional[str] = None
    created_at: Optional[datetime] = None
