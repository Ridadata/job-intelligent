"""Repository for the job_offers and dw_job_offers tables."""

from typing import Any

from supabase import Client


class JobRepository:
    """Data access layer for job offers (Silver + Gold).

    Args:
        client: Supabase client instance.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def find_by_id(self, job_id: str) -> dict[str, Any] | None:
        """Find a Silver job offer by UUID.

        Args:
            job_id: The job UUID.

        Returns:
            Job dict or None if not found.
        """
        result = (
            self._client.table("job_offers")
            .select(
                "id, source_id, raw_offer_id, title, company, location, description,"
                " contract_type, required_skills, published_at, salary_min, salary_max,"
                " created_at, updated_at"
            )
            .eq("id", job_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

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
    ) -> tuple[list[dict[str, Any]], int]:
        """List job offers with pagination and filters.

        Args:
            page: Page number (1-indexed).
            per_page: Results per page.
            q: Free-text search (matches title and company via ilike).
            location: Optional location filter.
            contract_type: Optional contract type filter.
            skills: Optional list of required skills (overlap match).
            salary_min: Minimum salary filter.
            salary_max: Maximum salary filter.

        Returns:
            Tuple of (items list, total count).
        """
        query = self._client.table("job_offers").select(
            "id, source_id, raw_offer_id, title, company, location, description,"
            " contract_type, required_skills, published_at, salary_min, salary_max,"
            " created_at, updated_at",
            count="exact",
        )

        if q:
            query = query.or_(f"title.ilike.%{q}%,company.ilike.%{q}%")
        if location:
            query = query.ilike("location", f"%{location}%")
        if contract_type:
            query = query.eq("contract_type", contract_type)
        if skills:
            query = query.overlaps("required_skills", skills)
        if salary_min is not None:
            query = query.gte("salary_min", salary_min)
        if salary_max is not None:
            query = query.lte("salary_max", salary_max)

        offset = (page - 1) * per_page
        query = query.order("published_at", desc=True).range(offset, offset + per_page - 1)

        result = query.execute()
        return result.data, result.count or 0

    def match_by_embedding(
        self,
        query_embedding: list[float],
        match_threshold: float = 0.70,
        match_count: int = 10,
        filter_contract: str | None = None,
        filter_location: str | None = None,
    ) -> list[dict[str, Any]]:
        """Find matching job offers using pgvector cosine similarity.

        Calls the match_job_offers SQL function defined in the Gold layer.

        Args:
            query_embedding: 384-dimensional embedding vector.
            match_threshold: Minimum cosine similarity score.
            match_count: Maximum number of results.
            filter_contract: Optional contract type filter.
            filter_location: Optional location filter.

        Returns:
            List of matching offer dicts with similarity scores.
        """
        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
        }
        if filter_contract:
            params["filter_contract"] = filter_contract
        if filter_location:
            params["filter_location"] = filter_location

        result = self._client.rpc("match_job_offers", params).execute()
        return result.data or []

    def log_recommendation_history(
        self,
        candidate_id: str,
        recommendations: list[dict[str, Any]],
    ) -> None:
        """Log recommendation results to the history table.

        Args:
            candidate_id: UUID of the candidate.
            recommendations: List of recommendation dicts with offer_id,
                similarity_score, and score_breakdown.
        """
        rows = [
            {
                "candidate_id": candidate_id,
                "job_offer_id": str(rec["offer_id"]),
                "similarity_score": rec.get("similarity_score", 0),
                "score_breakdown": rec.get("score_breakdown", {}),
                "action": "shown",
            }
            for rec in recommendations
        ]
        if rows:
            try:
                self._client.table("recommendation_history").insert(rows).execute()
            except Exception:
                # History logging is best-effort; don't fail the request
                import logging
                logging.getLogger(__name__).warning(
                    "Failed to log recommendation history for candidate %s",
                    candidate_id, exc_info=True,
                )
