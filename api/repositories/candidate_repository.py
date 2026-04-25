"""Repository for the candidate_profiles table."""

from typing import Any

from supabase import Client


class CandidateRepository:
    """Data access layer for candidate profiles.

    Args:
        client: Supabase client instance.
    """

    def __init__(self, client: Client) -> None:
        self._client = client
        self._table = "candidate_profiles"

    def find_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        """Find a candidate profile by user ID.

        Args:
            user_id: The associated user UUID.

        Returns:
            Profile dict or None if not found.
        """
        result = (
            self._client.table(self._table)
            .select(
                "id, user_id, name, title, skills, experience_years, education_level,"
                " location, salary_expectation, preferred_contract_types,"
                " profile_completeness, created_at, updated_at"
            )
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def find_by_id(self, candidate_id: str) -> dict[str, Any] | None:
        """Find a candidate profile by UUID.

        Args:
            candidate_id: The profile UUID.

        Returns:
            Profile dict or None if not found.
        """
        result = (
            self._client.table(self._table)
            .select(
                "id, user_id, name, title, skills, experience_years, education_level,"
                " location, salary_expectation, preferred_contract_types,"
                " profile_completeness, created_at, updated_at"
            )
            .eq("id", candidate_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new candidate profile.

        Args:
            user_id: The associated user UUID.
            data: Profile fields.

        Returns:
            Created profile dict.
        """
        data["user_id"] = user_id
        result = self._client.table(self._table).insert(data).execute()
        return result.data[0]

    def update(self, candidate_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing candidate profile.

        Args:
            candidate_id: The profile UUID.
            data: Fields to update.

        Returns:
            Updated profile dict.
        """
        result = (
            self._client.table(self._table)
            .update(data)
            .eq("id", candidate_id)
            .execute()
        )
        return result.data[0]
