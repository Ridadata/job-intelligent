"""Pydantic schemas for candidate profiles and CV uploads."""

from datetime import datetime

from pydantic import BaseModel


class CandidateProfileCreate(BaseModel):
    """Payload for creating a candidate profile.

    Attributes:
        name: Full name.
        title: Current or desired job title.
        skills: List of skill strings.
        experience_years: Years of professional experience.
        education_level: Highest education level.
        location: Preferred location.
        salary_expectation: Expected annual salary.
        preferred_contract_types: List of contract types.
    """

    name: str | None = None
    title: str | None = None
    skills: list[str] = []
    experience_years: int | None = None
    education_level: str | None = None
    location: str | None = None
    salary_expectation: float | None = None
    preferred_contract_types: list[str] = []


class CandidateProfileUpdate(CandidateProfileCreate):
    """Payload for updating a candidate profile (all fields optional)."""

    pass


class CandidateProfileResponse(BaseModel):
    """Public candidate profile representation.

    Attributes:
        id: Profile UUID.
        user_id: Associated user UUID.
        name: Full name.
        title: Job title.
        skills: Skills list.
        experience_years: Years of experience.
        education_level: Education level.
        location: Location.
        salary_expectation: Salary expectation.
        preferred_contract_types: Contract preferences.
        profile_completeness: Completeness percentage (0-100).
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    user_id: str
    name: str | None = None
    title: str | None = None
    skills: list[str] = []
    experience_years: int | None = None
    education_level: str | None = None
    location: str | None = None
    salary_expectation: float | None = None
    preferred_contract_types: list[str] = []
    profile_completeness: int = 0
    created_at: datetime
    updated_at: datetime


class CVUploadResponse(BaseModel):
    """Response after CV upload.

    Attributes:
        id: CV document UUID.
        file_type: pdf or docx.
        parsing_status: Current parsing status.
        message: Human-readable status message.
    """

    id: str
    file_type: str
    parsing_status: str
    message: str


class CVDocumentResponse(BaseModel):
    """Full CV document details.

    Attributes:
        id: Document UUID.
        candidate_id: Associated candidate UUID.
        file_type: pdf or docx.
        parsed_skills: Extracted skills.
        parsed_experience: Extracted experience text.
        parsed_education: Extracted education text.
        parsing_status: Current status.
        parsed_at: When parsing completed.
    """

    id: str
    candidate_id: str
    file_type: str
    parsed_skills: list[str] = []
    parsed_experience: str | None = None
    parsed_education: str | None = None
    parsing_status: str
    parsed_at: datetime | None = None
