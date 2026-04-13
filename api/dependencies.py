"""FastAPI dependencies — database, auth, role guard, service factories."""

import logging
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from supabase import Client, create_client

from api.config import api_settings
from api.core.security import decode_access_token
from api.repositories.candidate_repository import CandidateRepository
from api.repositories.cv_repository import CVDocumentRepository
from api.repositories.job_repository import JobRepository
from api.repositories.saved_jobs_repository import SavedJobsRepository
from api.repositories.user_repository import UserRepository
from api.services.auth_service import AuthService
from api.services.candidate_service import CandidateService
from api.services.job_service import JobService

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None


# ── Database ─────────────────────────────────────────────────────────────────

def get_db() -> Client:
    """Get the Supabase client (singleton).

    Returns:
        Client: The Supabase client instance.
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            api_settings.supabase_url,
            api_settings.supabase_key,
        )
    return _supabase_client


# ── Authentication ───────────────────────────────────────────────────────────

async def get_current_user(request: Request) -> dict[str, Any]:
    """Extract and validate JWT token from Authorization header.

    Decodes the token using the app's JWT secret and returns user claims.
    Falls back to Supabase Auth validation if local decode fails.

    Args:
        request: The incoming FastAPI request.

    Returns:
        Dict with user id, email, and role.

    Raises:
        HTTPException: If token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.removeprefix("Bearer ").strip()

    # Try local JWT decode first (for tokens we issued)
    try:
        payload = decode_access_token(token)
        return {
            "id": payload["sub"],
            "email": payload.get("email", ""),
            "role": payload.get("role", "candidate"),
        }
    except (JWTError, KeyError):
        pass

    # Fallback: Supabase Auth token
    try:
        client = get_db()
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "role": "candidate",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Auth validation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from exc


def require_role(*roles: str):
    """Create a dependency that enforces one or more required roles.

    Args:
        roles: Allowed role names (e.g., "admin", "candidate").

    Returns:
        Dependency function that validates user role.
    """
    async def _check_role(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.get('role')}' not authorized. Required: {', '.join(roles)}",
            )
        return current_user
    return _check_role


# ── Service factories ────────────────────────────────────────────────────────

def get_auth_service(db: Client = Depends(get_db)) -> AuthService:
    """Build AuthService with injected repository.

    Args:
        db: Supabase client.

    Returns:
        AuthService instance.
    """
    return AuthService(user_repo=UserRepository(db))


def get_job_service(db: Client = Depends(get_db)) -> JobService:
    """Build JobService with injected repositories.

    Args:
        db: Supabase client.

    Returns:
        JobService instance.
    """
    return JobService(
        job_repo=JobRepository(db),
        saved_repo=SavedJobsRepository(db),
        candidate_repo=CandidateRepository(db),
    )


def get_candidate_service(db: Client = Depends(get_db)) -> CandidateService:
    """Build CandidateService with injected repositories.

    Args:
        db: Supabase client.

    Returns:
        CandidateService instance.
    """
    return CandidateService(
        candidate_repo=CandidateRepository(db),
        cv_repo=CVDocumentRepository(db),
        cv_upload_dir=api_settings.cv_upload_dir,
        max_cv_size=api_settings.max_cv_size_bytes,
    )
