"""Pydantic schemas for recommendations and matching.

Canonical recommendation schemas live in api.models.schemas.
This module re-exports them and adds supplementary schemas
(MatchExplanation, SkillGapResponse) used by the skill-gap endpoint.
"""

from typing import Optional

from pydantic import BaseModel

# Re-export canonical recommendation schemas so imports from either
# location work without duplication.
from api.models.schemas import (  # noqa: F401
    JobOfferMatch,
    RecommendationFilters,
    RecommendationMeta,
    RecommendationRequest,
    RecommendationResponse,
)


class MatchExplanation(BaseModel):
    """Detailed explanation of a match score.

    Attributes:
        matched_skills: Skills present in both candidate and job.
        missing_skills: Job skills the candidate lacks.
        score_breakdown: Breakdown of composite score components.
    """

    matched_skills: list[str] = []
    missing_skills: list[str] = []
    score_breakdown: dict[str, float] = {}


class SkillGapResponse(BaseModel):
    """Skill gap analysis for a candidate.

    Attributes:
        candidate_skills: Current candidate skills.
        top_missing_skills: Most in-demand skills the candidate lacks.
        skill_frequency: How often each missing skill appears in job offers.
        improvement_potential: Percentage of jobs requiring each missing skill.
        latency_ms: Processing time in milliseconds.
    """

    candidate_skills: list[str] = []
    top_missing_skills: list[str] = []
    skill_frequency: dict[str, int] = {}
    improvement_potential: dict[str, float] = {}
    latency_ms: Optional[int] = None
