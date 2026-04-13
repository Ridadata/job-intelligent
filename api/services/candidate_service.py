"""Candidate service — profile CRUD and CV upload orchestration.

Contains all candidate-related business logic. Never imports FastAPI types.
"""

import logging
import math
import os
from typing import Any

from api.core.exceptions import NotFoundError, ValidationError
from api.repositories.candidate_repository import CandidateRepository
from api.repositories.cv_repository import CVDocumentRepository

logger = logging.getLogger(__name__)


_PROFILE_FIELDS = [
    "name", "title", "skills", "experience_years",
    "education_level", "location", "salary_expectation",
    "preferred_contract_types",
]


class CandidateService:
    """Handles candidate profile management and CV uploads.

    Args:
        candidate_repo: CandidateRepository instance.
        cv_repo: CVDocumentRepository instance.
        cv_upload_dir: Directory for CV file storage.
        max_cv_size: Maximum CV file size in bytes.
    """

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        cv_repo: CVDocumentRepository,
        cv_upload_dir: str = "cv_uploads",
        max_cv_size: int = 5_242_880,
    ) -> None:
        self._candidate_repo = candidate_repo
        self._cv_repo = cv_repo
        self._cv_upload_dir = cv_upload_dir
        self._max_cv_size = max_cv_size

    def get_profile(self, user_id: str) -> dict[str, Any]:
        """Get a candidate's profile by user ID.

        Args:
            user_id: The associated user UUID.

        Returns:
            Profile dict.

        Raises:
            NotFoundError: If profile doesn't exist.
        """
        profile = self._candidate_repo.find_by_user_id(user_id)
        if not profile:
            raise NotFoundError("CandidateProfile", user_id)
        return profile

    def create_profile(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new candidate profile.

        Args:
            user_id: The associated user UUID.
            data: Profile fields.

        Returns:
            Created profile dict with completeness score.
        """
        clean = {k: v for k, v in data.items() if k in _PROFILE_FIELDS and v is not None}
        clean["profile_completeness"] = _compute_completeness(clean)
        profile = self._candidate_repo.create(user_id=user_id, data=clean)
        self._update_embedding(profile)
        return profile

    def update_profile(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing candidate profile.

        Args:
            user_id: The associated user UUID.
            data: Fields to update (partial).

        Returns:
            Updated profile dict.

        Raises:
            NotFoundError: If profile doesn't exist.
        """
        profile = self._candidate_repo.find_by_user_id(user_id)
        if not profile:
            raise NotFoundError("CandidateProfile", user_id)

        clean = {k: v for k, v in data.items() if k in _PROFILE_FIELDS and v is not None}
        if not clean:
            return profile

        # Merge to compute new completeness
        merged = {**profile, **clean}
        clean["profile_completeness"] = _compute_completeness(merged)
        updated = self._candidate_repo.update(candidate_id=profile["id"], data=clean)
        self._update_embedding(updated)
        return updated

    def _update_embedding(self, profile: dict[str, Any]) -> None:
        """Generate and store the candidate embedding vector.

        Args:
            profile: The candidate profile dict (must have 'id').
        """
        skills = profile.get("skills") or []
        title = profile.get("title") or ""
        if not skills:
            return
        try:
            from ai_services.embedding.generator import generate_embedding

            skills_text = ", ".join(skills)
            text = f"{title}. Skills: {skills_text}" if title else f"Skills: {skills_text}"
            embedding = generate_embedding(text)
            self._candidate_repo.update(
                candidate_id=profile["id"],
                data={"embedding": embedding},
            )
            logger.info("Updated embedding for candidate %s", profile["id"])
        except Exception:
            logger.warning(
                "Failed to generate embedding for candidate %s — skipping",
                profile["id"],
                exc_info=True,
            )

    def upload_cv(
        self, user_id: str, filename: str, content: bytes, content_type: str
    ) -> dict[str, Any]:
        """Accept a CV upload and queue it for parsing.

        Args:
            user_id: The associated user UUID.
            filename: Original filename.
            content: File bytes.
            content_type: MIME type.

        Returns:
            CV document record with pending status.

        Raises:
            NotFoundError: If candidate profile doesn't exist.
            ValidationError: If file type or size is invalid.
        """
        profile = self._candidate_repo.find_by_user_id(user_id)
        if not profile:
            raise NotFoundError("CandidateProfile", user_id)

        if len(content) > self._max_cv_size:
            raise ValidationError(f"File too large. Max size: {self._max_cv_size // 1_048_576} MB")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ("pdf", "docx"):
            raise ValidationError("Only PDF and DOCX files are accepted")

        os.makedirs(self._cv_upload_dir, exist_ok=True)
        file_path = os.path.join(self._cv_upload_dir, f"{profile['id']}_{filename}")
        with open(file_path, "wb") as f:
            f.write(content)

        return self._cv_repo.create(
            candidate_id=profile["id"],
            file_path=file_path,
            file_type=ext,
        )


def _compute_completeness(data: dict[str, Any]) -> int:
    """Compute profile completeness percentage.

    Args:
        data: Profile fields dict.

    Returns:
        Integer 0-100.
    """
    total = len(_PROFILE_FIELDS)
    filled = 0
    for field in _PROFILE_FIELDS:
        value = data.get(field)
        if value is not None and value != "" and value != []:
            filled += 1
    return int((filled / total) * 100)
