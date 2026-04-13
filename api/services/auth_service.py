"""Authentication service — register, login, profile lookup.

Contains all auth business logic. Never imports FastAPI types.
Raises domain exceptions (AuthenticationError, DuplicateError, NotFoundError).
"""

from typing import Any

from api.core.exceptions import AuthenticationError, DuplicateError, NotFoundError
from api.core.security import create_access_token, hash_password, verify_password
from api.repositories.user_repository import UserRepository


class AuthService:
    """Handles user registration, login, and profile retrieval.

    Args:
        user_repo: UserRepository instance.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def register(self, email: str, password: str) -> dict[str, Any]:
        """Register a new user account.

        Args:
            email: User email (must be unique, stored lowercase).
            password: Plaintext password (will be hashed).

        Returns:
            Created user dict (password_hash excluded).

        Raises:
            DuplicateError: If email already registered.
        """
        email = email.lower().strip()
        existing = self._user_repo.find_by_email(email)
        if existing:
            raise DuplicateError("User", "email")

        hashed = hash_password(password)
        user = self._user_repo.create(email=email, password_hash=hashed)
        user.pop("password_hash", None)
        return user

    def login(self, email: str, password: str) -> str:
        """Authenticate a user and return a JWT token.

        Args:
            email: User email.
            password: Plaintext password.

        Returns:
            JWT access token string.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        user = self._user_repo.find_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid email or password")

        return create_access_token(
            data={"sub": user["id"], "email": user["email"], "role": user.get("role", "candidate")}
        )

    def get_profile(self, user_id: str) -> dict[str, Any]:
        """Get user profile by ID.

        Args:
            user_id: User UUID.

        Returns:
            User dict (without password_hash).

        Raises:
            NotFoundError: If user doesn't exist.
        """
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)

        user.pop("password_hash", None)
        return user
