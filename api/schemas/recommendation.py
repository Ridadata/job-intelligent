"""Pydantic schemas for recommendations and matching."""

from pydantic import BaseModel


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


class RecommendationResponse(BaseModel):
    """A single job recommendation for a candidate.

    Attributes:
        job_id: The recommended job UUID.
        title: Job title.
        company: Company name.
        location: Job location.
        similarity_score: Overall match score (0-1).
        explanation: Detailed match explanation.
    """

    job_id: str
    title: str
    company: str | None = None
    location: str | None = None
    similarity_score: float
    explanation: MatchExplanation


class SkillGapResponse(BaseModel):
    """Skill gap analysis for a candidate.

    Attributes:
        candidate_skills: Current candidate skills.
        top_missing_skills: Most in-demand skills the candidate lacks.
        skill_frequency: How often each missing skill appears in job offers.
    """

    candidate_skills: list[str] = []
    top_missing_skills: list[str] = []
    skill_frequency: dict[str, int] = {}
