"""Repository for the cv_documents table."""

import datetime
from typing import Any

from supabase import Client


class CVDocumentRepository:
    """Data access layer for CV documents.

    Args:
        client: Supabase client instance.
    """

    def __init__(self, client: Client) -> None:
        self._client = client
        self._table = "cv_documents"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new CV document record.

        Args:
            data: Document fields (candidate_id, file_path, file_type, etc).

        Returns:
            Created document dict.
        """
        result = self._client.table(self._table).insert(data).execute()
        return result.data[0]

    def update_parsing_result(
        self,
        doc_id: str,
        status: str,
        parsed_skills: list[str] | None = None,
        parsed_experience: str | None = None,
        parsed_education: str | None = None,
        raw_text: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update CV parsing results.

        Args:
            doc_id: The CV document UUID.
            status: New parsing status.
            parsed_skills: Extracted skills list.
            parsed_experience: Extracted experience text.
            parsed_education: Extracted education text.
            raw_text: Full extracted text.
            error: Error message if parsing failed.

        Returns:
            Updated document dict.
        """
        data: dict[str, Any] = {"parsing_status": status}
        if parsed_skills is not None:
            data["parsed_skills"] = parsed_skills
        if parsed_experience is not None:
            data["parsed_experience"] = parsed_experience
        if parsed_education is not None:
            data["parsed_education"] = parsed_education
        if raw_text is not None:
            data["raw_text"] = raw_text
        if error is not None:
            data["parsing_error"] = error
        if status == "success":
            data["parsed_at"] = datetime.datetime.utcnow().isoformat()

        result = self._client.table(self._table).update(data).eq("id", doc_id).execute()
        return result.data[0]

    def find_by_candidate(self, candidate_id: str) -> list[dict[str, Any]]:
        """List all CV documents for a candidate.

        Args:
            candidate_id: The candidate profile UUID.

        Returns:
            List of CV document dicts.
        """
        result = (
            self._client.table(self._table)
            .select("*")
            .eq("candidate_id", candidate_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
