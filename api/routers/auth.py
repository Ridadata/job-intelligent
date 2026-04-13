"""Authentication router — register, login, profile endpoints."""

import logging

from fastapi import APIRouter, Depends, status

from api.dependencies import get_auth_service, get_current_user
from api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from api.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Create a new user account.

    Args:
        body: Registration payload with email and password.
        auth_service: Injected auth service.

    Returns:
        Created user profile.
    """
    user = auth_service.register(email=body.email, password=body.password)
    return UserResponse(id=user["id"], email=user["email"], role=user.get("role", "candidate"))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT token",
)
def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate and return a JWT access token.

    Args:
        body: Login payload with email and password.
        auth_service: Injected auth service.

    Returns:
        JWT token response.
    """
    token = auth_service.login(email=body.email, password=body.password)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def me(
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    """Return the authenticated user's profile.

    Args:
        current_user: Injected from JWT validation.

    Returns:
        Current user profile.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user.get("role", "candidate"),
    )
