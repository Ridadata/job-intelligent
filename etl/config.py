"""Centralized configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    supabase_url: str = field(default_factory=lambda: os.environ["SUPABASE_URL"])
    supabase_key: str = field(default_factory=lambda: os.environ["SUPABASE_KEY"])
    supabase_db_url: str = field(
        default_factory=lambda: os.environ.get("SUPABASE_DB_URL", "")
    )
    redis_url: str = field(
        default_factory=lambda: os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    )
    sbert_model: str = field(
        default_factory=lambda: os.environ.get("SBERT_MODEL", "all-MiniLM-L6-v2")
    )
    spacy_model: str = field(
        default_factory=lambda: os.environ.get("SPACY_MODEL", "fr_core_news_md")
    )
    etl_batch_size: int = field(
        default_factory=lambda: int(os.environ.get("ETL_BATCH_SIZE", "100"))
    )


settings = Settings()
