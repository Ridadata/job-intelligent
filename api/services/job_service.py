"""Job service — search, detail, and save operations.

Contains all job-related business logic. Never imports FastAPI types.
"""

import math
from typing import Any

from api.core.exceptions import NotFoundError
from api.repositories.candidate_repository import CandidateRepository
from api.repositories.job_repository import JobRepository
from api.repositories.saved_jobs_repository import SavedJobsRepository


class JobService:
    """Handles job listing, detail retrieval, and bookmarking.

    Args:
        job_repo: JobRepository instance.
        saved_repo: SavedJobsRepository instance.
        candidate_repo: CandidateRepository instance (needed to resolve profile from user_id).
    """

    def __init__(
        self,
        job_repo: JobRepository,
        saved_repo: SavedJobsRepository,
        candidate_repo: CandidateRepository,
    ) -> None:
        self._job_repo = job_repo
        self._saved_repo = saved_repo
        self._candidate_repo = candidate_repo

    def _resolve_candidate_id(self, user_id: str) -> str:
        """Resolve the candidate profile UUID from an authenticated user ID.

        Args:
            user_id: Authenticated user UUID (from JWT).

        Returns:
            Candidate profile UUID.

        Raises:
            NotFoundError: If no candidate profile exists for this user.
        """
        profile = self._candidate_repo.find_by_user_id(user_id)
        if not profile:
            raise NotFoundError("CandidateProfile", user_id)
        return profile["id"]

    def get_by_id(self, job_id: str) -> dict[str, Any]:
        """Get a single job offer by ID.

        Args:
            job_id: Job UUID.

        Returns:
            Job dict.

        Raises:
            NotFoundError: If job doesn't exist.
        """
        job = self._job_repo.find_by_id(job_id)
        if not job:
            raise NotFoundError("Job", job_id)
        return job

    def list_jobs(
        self,
        page: int = 1,
        per_page: int = 20,
        q: str | None = None,
        location: str | None = None,
        contract_type: str | None = None,
        skills: list[str] | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
    ) -> dict[str, Any]:
        """List jobs with pagination and optional filters.

        Args:
            page: Page number (1-indexed).
            per_page: Results per page (max 100).
            q: Free-text search query.
            location: Optional location filter.
            contract_type: Optional contract type filter.
            skills: Optional list of required skills.
            salary_min: Minimum salary filter.
            salary_max: Maximum salary filter.

        Returns:
            Dict with items, total, page, per_page, pages.
        """
        per_page = min(per_page, 100)
        items, total = self._job_repo.list_jobs(
            page=page,
            per_page=per_page,
            q=q,
            location=location,
            contract_type=contract_type,
            skills=skills,
            salary_min=salary_min,
            salary_max=salary_max,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if per_page else 0,
        }

    def save_job(self, user_id: str, job_id: str) -> dict[str, Any]:
        """Save a job offer for the authenticated user.

        Args:
            user_id: Authenticated user UUID (resolved to candidate profile internally).
            job_id: Job offer UUID.

        Returns:
            Saved job record.

        Raises:
            NotFoundError: If job or candidate profile doesn't exist.
        """
        job = self._job_repo.find_by_id(job_id)
        if not job:
            raise NotFoundError("Job", job_id)
        candidate_id = self._resolve_candidate_id(user_id)
        return self._saved_repo.save(candidate_id=candidate_id, job_offer_id=job_id)

    def unsave_job(self, user_id: str, job_id: str) -> None:
        """Remove a saved job bookmark.

        Args:
            user_id: Authenticated user UUID.
            job_id: Job offer UUID.
        """
        candidate_id = self._resolve_candidate_id(user_id)
        self._saved_repo.unsave(candidate_id=candidate_id, job_offer_id=job_id)

    def list_saved_jobs(
        self, user_id: str, page: int = 1, per_page: int = 20
    ) -> dict[str, Any]:
        """List saved jobs for the authenticated user.

        Args:
            user_id: Authenticated user UUID.
            page: Page number.
            per_page: Results per page.

        Returns:
            Paginated response dict with flattened job items.
        """
        candidate_id = self._resolve_candidate_id(user_id)
        per_page = min(per_page, 100)
        items, total = self._saved_repo.list_saved(
            candidate_id=candidate_id, page=page, per_page=per_page
        )
        # Flatten: repo returns {candidate_id, job_offer_id, saved_at, job_offers: {...}}
        # Extract the nested job_offers dict so frontend gets flat Job objects
        flat_items = []
        for item in items:
            job_data = item.get("job_offers")
            if job_data and isinstance(job_data, dict):
                flat_items.append(job_data)
        return {
            "items": flat_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if per_page else 0,
        }
