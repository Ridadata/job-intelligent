"""Candidate service — profile CRUD and CV upload orchestration.

Contains all candidate-related business logic. Never imports FastAPI types.
"""

import logging
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

        doc = self._cv_repo.create({
            "candidate_id": profile["id"],
            "file_path": file_path,
            "file_type": ext,
            "parsing_status": "pending",
        })
        return doc

    def parse_cv_background(self, doc_id: str, file_path: str, candidate_id: str) -> None:
        """Parse a CV file in the background and enrich the candidate profile.

        Extracts text, runs NLP pipeline, updates cv_documents, and merges
        parsed data into candidate_profiles. Never raises — logs errors instead.

        Args:
            doc_id: CV document UUID.
            file_path: Path to the saved CV file.
            candidate_id: Candidate profile UUID to enrich.
        """
        try:
            from ai_services.cv_parser.extractor import extract_text
            from ai_services.cv_parser.enrichment import parse_cv

            raw_text = extract_text(file_path)
            parsed = parse_cv(raw_text)

            self._cv_repo.update_parsing_result(
                doc_id=doc_id,
                status="success",
                parsed_skills=parsed.get("skills") or [],
                parsed_experience=parsed.get("experience"),
                parsed_education=parsed.get("education"),
                raw_text=raw_text,
            )

            # Enrich candidate profile — union skills, keep max experience
            profile = self._candidate_repo.find_by_id(candidate_id)
            if profile:
                new_skills = parsed.get("skills") or []
                existing_skills = profile.get("skills") or []
                merged_skills = sorted(set(existing_skills) | set(new_skills))

                update_data: dict[str, Any] = {}
                if merged_skills:
                    update_data["skills"] = merged_skills

                exp_text = parsed.get("experience")
                if exp_text:
                    import re
                    m = re.search(r"(\d+)", exp_text)
                    if m:
                        parsed_years = int(m.group(1))
                        current_years = profile.get("experience_years") or 0
                        if parsed_years > current_years:
                            update_data["experience_years"] = parsed_years

                if parsed.get("education") and not profile.get("education_level"):
                    update_data["education_level"] = parsed["education"]

                if update_data:
                    merged = {**profile, **update_data}
                    update_data["profile_completeness"] = _compute_completeness(merged)
                    updated = self._candidate_repo.update(
                        candidate_id=candidate_id, data=update_data
                    )
                    self._update_embedding(updated)
                    logger.info("Enriched candidate %s from CV parsing", candidate_id)

        except Exception:
            logger.error("CV parsing failed for doc %s", doc_id, exc_info=True)
            try:
                import traceback
                self._cv_repo.update_parsing_result(
                    doc_id=doc_id,
                    status="failed",
                    error=traceback.format_exc(),
                )
            except Exception:
                pass


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
