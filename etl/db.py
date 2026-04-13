"""Async Supabase client singleton."""

import logging
from typing import Optional

from supabase import create_client, Client

from etl.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return a Supabase client, creating one if it doesn't exist.

    Returns:
        Client: The Supabase client instance.
    """
    global _client
    if _client is None:
        logger.info("Initializing Supabase client for %s", settings.supabase_url)
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def reset_client() -> None:
    """Reset the cached client (useful for testing)."""
    global _client
    _client = None
