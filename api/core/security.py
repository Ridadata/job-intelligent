"""JWT token creation and verification utilities.

Uses python-jose for JWT encoding/decoding and passlib for password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from api.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password.

    Returns:
        The bcrypt hash string.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain: The plaintext password.
        hashed: The stored bcrypt hash.

    Returns:
        True if the password matches.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload to encode (must include 'sub').
        expires_delta: Optional custom expiration. Defaults to config value.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT string.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
