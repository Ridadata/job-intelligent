"""Centralized application configuration via Pydantic BaseSettings.

All backend code should access config through get_settings() dependency.
Never use os.environ directly in business code.
"""

from functools import lru_cache
import logging

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        supabase_url: Supabase project URL.
        supabase_key: Supabase service-role key.
        redis_url: Redis connection URL.
        sbert_model: Sentence-BERT model name.
        spacy_model: spaCy model name for NLP.
        jwt_secret_key: Secret key for JWT token signing.
        jwt_algorithm: Algorithm for JWT encoding.
        jwt_expire_minutes: Token expiration in minutes.
        api_host: API server host.
        api_port: API server port.
        api_debug: Enable debug mode.
        max_cv_size_bytes: Maximum CV upload size.
        cv_upload_dir: Directory for CV file storage.
    """

    supabase_url: str
    supabase_key: str
    redis_url: str = "redis://localhost:6379/0"
    sbert_model: str = "all-MiniLM-L6-v2"
    spacy_model: str = "fr_core_news_md"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    max_cv_size_bytes: int = 5_242_880  # 5 MB
    cv_upload_dir: str = "cv_uploads"
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"

    @field_validator("jwt_secret_key")
    @classmethod
    def _warn_insecure_jwt_secret(cls, v: str) -> str:
        """Warn if the JWT secret is using the insecure default."""
        if v == "change-me-in-production":
            logging.getLogger(__name__).warning(
                "JWT_SECRET_KEY is using the insecure default — set it via environment variable"
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton.

    Returns:
        Settings instance loaded from environment.
    """
    return Settings()  # type: ignore[call-arg]


# Convenience singleton — same object as get_settings(), usable without Depends()
api_settings: Settings = get_settings()
