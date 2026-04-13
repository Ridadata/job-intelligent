"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """User registration payload.

    Attributes:
        email: User's email address.
        password: Plaintext password (min 8 chars).
    """

    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """User login payload.

    Attributes:
        email: User's email address.
        password: Plaintext password.
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response.

    Attributes:
        access_token: The JWT string.
        token_type: Always 'bearer'.
    """

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user representation.

    Attributes:
        id: User UUID.
        email: User email.
        role: User role (candidate or admin).
    """

    id: str
    email: str
    role: str
