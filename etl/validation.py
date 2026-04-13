"""Pydantic schema validation for ETL pipeline layers.

Validates data at each Bronze→Silver→Gold boundary to reject malformed
rows with clear error messages before they reach the database.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ── Bronze layer validation ──────────────────────────────────────────────────

class RawOfferSchema(BaseModel):
    """Schema for a raw offer before Bronze ingestion.

    Validates that the minimum required fields exist in the scraped data.
    """

    external_id: str = Field(..., min_length=1)
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None

    @field_validator("external_id")
    @classmethod
    def strip_external_id(cls, v: str) -> str:
        """Strip whitespace from external_id.

        Args:
            v: The raw external_id string.

        Returns:
            Stripped string.
        """
        return v.strip()


# ── Silver layer validation ──────────────────────────────────────────────────

class SilverOfferSchema(BaseModel):
    """Schema for a validated Silver-layer offer.

    Enforces data quality before insertion into job_offers table.
    """

    source_id: str
    raw_offer_id: str
    title: str = Field(..., min_length=1, max_length=500)
    company: Optional[str] = Field(None, max_length=300)
    location: Optional[str] = Field(None, max_length=300)
    contract_type: str = Field(default="Autre")
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    required_skills: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    published_at: Optional[str] = None

    @field_validator("contract_type")
    @classmethod
    def validate_contract_type(cls, v: str) -> str:
        """Ensure contract_type is one of the allowed values.

        Args:
            v: The contract type string.

        Returns:
            Validated contract type.

        Raises:
            ValueError: If contract_type is not in the allowed set.
        """
        allowed = {"CDI", "CDD", "Freelance", "Stage", "Alternance", "Autre"}
        if v not in allowed:
            raise ValueError(f"Invalid contract_type '{v}', must be one of {allowed}")
        return v

    @field_validator("salary_max")
    @classmethod
    def salary_max_gte_min(cls, v: Optional[float], info: Any) -> Optional[float]:
        """Ensure salary_max >= salary_min when both are present.

        Args:
            v: The salary_max value.
            info: Validation info containing other field values.

        Returns:
            Validated salary_max.
        """
        salary_min = info.data.get("salary_min")
        if v is not None and salary_min is not None and v < salary_min:
            v, salary_min = salary_min, v  # auto-swap
        return v

    @field_validator("required_skills")
    @classmethod
    def deduplicate_skills(cls, v: list[str]) -> list[str]:
        """Ensure skills are deduplicated and sorted.

        Args:
            v: List of skill strings.

        Returns:
            Sorted deduplicated list.
        """
        return sorted(set(v))


# ── Gold layer validation ────────────────────────────────────────────────────

class GoldOfferSchema(BaseModel):
    """Schema for a validated Gold-layer enriched offer.

    Enforces that embeddings and NLP fields are valid before insertion
    into dw_job_offers.
    """

    offer_id: str
    embedding: list[float] = Field(..., min_length=384, max_length=384)
    normalized_title: str = Field(..., min_length=1)
    seniority_level: str = Field(default="Mid")
    tech_stack: list[str] = Field(default_factory=list)
    demand_score: float = Field(..., ge=0.0, le=1.0)
    category: Optional[str] = None
    contract_type_standardized: Optional[str] = None
    dedup_key: Optional[str] = None

    @field_validator("seniority_level")
    @classmethod
    def validate_seniority(cls, v: str) -> str:
        """Ensure seniority_level is one of the allowed values.

        Args:
            v: The seniority level string.

        Returns:
            Validated seniority level.

        Raises:
            ValueError: If seniority_level is not in the allowed set.
        """
        allowed = {"Junior", "Mid", "Senior"}
        if v not in allowed:
            raise ValueError(f"Invalid seniority_level '{v}', must be one of {allowed}")
        return v

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v: list[float]) -> list[float]:
        """Ensure embedding has no NaN or infinite values.

        Args:
            v: The embedding vector.

        Returns:
            Validated embedding.

        Raises:
            ValueError: If embedding contains invalid values.
        """
        import math
        for i, val in enumerate(v):
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Embedding contains invalid value at index {i}: {val}")
        return v


def validate_silver_row(row: dict[str, Any]) -> tuple[bool, dict[str, Any] | str]:
    """Validate a single Silver row against the schema.

    Args:
        row: Dictionary with Silver-layer fields.

    Returns:
        Tuple of (is_valid, validated_dict_or_error_message).
    """
    try:
        validated = SilverOfferSchema(**row)
        return True, validated.model_dump()
    except Exception as e:
        return False, str(e)


def validate_gold_row(row: dict[str, Any]) -> tuple[bool, dict[str, Any] | str]:
    """Validate a single Gold row against the schema.

    Args:
        row: Dictionary with Gold-layer fields.

    Returns:
        Tuple of (is_valid, validated_dict_or_error_message).
    """
    try:
        validated = GoldOfferSchema(**row)
        return True, validated.model_dump()
    except Exception as e:
        return False, str(e)
