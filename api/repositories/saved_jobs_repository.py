"""Repository for the saved_jobs table."""

from typing import Any

from supabase import Client


class SavedJobsRepository:
    """Data access layer for saved/bookmarked jobs.

    Args:
        client: Supabase client instance.
    """

    def __init__(self, client: Client) -> None:
        self._client = client
        self._table = "saved_jobs"

    def save(self, candidate_id: str, job_offer_id: str) -> dict[str, Any]:
        """Save a job offer for a candidate.

        Args:
            candidate_id: The candidate profile UUID.
            job_offer_id: The job offer UUID.

        Returns:
            Created saved job dict.
        """
        result = (
            self._client.table(self._table)
            .upsert(
                {"candidate_id": candidate_id, "job_offer_id": job_offer_id},
                on_conflict="candidate_id,job_offer_id",
            )
            .execute()
        )
        return result.data[0]

    def unsave(self, candidate_id: str, job_offer_id: str) -> None:
        """Remove a saved job.

        Args:
            candidate_id: The candidate profile UUID.
            job_offer_id: The job offer UUID.
        """
        self._client.table(self._table).delete().eq(
            "candidate_id", candidate_id
        ).eq("job_offer_id", job_offer_id).execute()

    def list_saved(
        self, candidate_id: str, page: int = 1, per_page: int = 20
    ) -> tuple[list[dict[str, Any]], int]:
        """List saved jobs for a candidate with pagination.

        Args:
            candidate_id: The candidate profile UUID.
            page: Page number (1-indexed).
            per_page: Results per page.

        Returns:
            Tuple of (items list, total count).
        """
        offset = (page - 1) * per_page
        result = (
            self._client.table(self._table)
            .select(
                "id, candidate_id, job_offer_id, saved_at,"
                " job_offers(id, title, company, location, contract_type,"
                " required_skills, salary_min, salary_max, published_at)",
                count="exact",
            )
            .eq("candidate_id", candidate_id)
            .order("saved_at", desc=True)
            .range(offset, offset + per_page - 1)
            .execute()
        )
        return result.data, result.count or 0
