"""Pydantic schemas for job endpoints."""

from datetime import datetime

from pydantic import BaseModel, field_validator


class JobResponse(BaseModel):
    """Public job offer representation.

    Attributes:
        id: Job UUID.
        title: Job title.
        company: Company name.
        location: Job location.
        contract_type: Contract type.
        salary_min: Minimum salary.
        salary_max: Maximum salary.
        required_skills: List of required skills.
        description: Job description.
        published_at: Publication date.
        taxonomy_category: Taxonomy category (from Gold layer, if available).
        url: External job URL (if available).
    """

    id: str
    title: str
    company: str | None = None
    location: str | None = None
    contract_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    required_skills: list[str] = []
    description: str | None = None
    published_at: datetime | None = None
    taxonomy_category: str | None = None
    url: str | None = None

    @field_validator("required_skills", mode="before")
    @classmethod
    def coerce_skills(cls, v: list[str] | None) -> list[str]:
        """Coerce NULL skills from DB to empty list."""
        return v if v is not None else []


class JobSearchParams(BaseModel):
    """Query parameters for job search.

    Attributes:
        q: Search query string.
        location: Filter by location.
        contract_type: Filter by contract type.
        skills: Filter by required skills.
        page: Page number (1-indexed).
        per_page: Results per page.
    """

    q: str | None = None
    location: str | None = None
    contract_type: str | None = None
    skills: list[str] = []
    page: int = 1
    per_page: int = 20
