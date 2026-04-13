"""Repository for the users table."""

from typing import Any

from supabase import Client


class UserRepository:
    """Data access layer for user accounts.

    Args:
        client: Supabase client instance.
    """

    def __init__(self, client: Client) -> None:
        self._client = client
        self._table = "users"

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        """Find a user by email address.

        Args:
            email: The email to look up.

        Returns:
            User dict or None if not found.
        """
        result = (
            self._client.table(self._table)
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Find a user by UUID.

        Args:
            user_id: The user UUID.

        Returns:
            User dict or None if not found.
        """
        result = (
            self._client.table(self._table)
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def create(self, email: str, password_hash: str, role: str = "candidate") -> dict[str, Any]:
        """Create a new user account.

        Args:
            email: User email.
            password_hash: Bcrypt hashed password.
            role: User role (candidate or admin).

        Returns:
            Created user dict.
        """
        result = (
            self._client.table(self._table)
            .insert({"email": email, "password_hash": password_hash, "role": role})
            .execute()
        )
        return result.data[0]
