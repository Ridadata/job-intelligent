"""Redis cache service for recommendation results."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from api.config import api_settings

logger = logging.getLogger(__name__)

_pool: Optional[redis.Redis] = None

CACHE_TTL_SECONDS: int = 3600  # 1 hour


async def get_redis_client() -> redis.Redis:
    """Get or create the async Redis client.

    Returns:
        redis.Redis: The async Redis client instance.
    """
    global _pool
    if _pool is None:
        logger.info("Connecting to Redis at %s", api_settings.redis_url)
        _pool = redis.from_url(
            api_settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _pool


async def get_cached(key: str) -> Optional[dict[str, Any]]:
    """Retrieve a cached value by key.

    Args:
        key: The cache key.

    Returns:
        The cached dict, or None if not found or expired.
    """
    try:
        client = await get_redis_client()
        raw = await client.get(key)
        if raw:
            logger.debug("Cache hit: %s", key)
            return json.loads(raw)
    except Exception:
        logger.warning("Redis GET failed for key '%s'", key, exc_info=True)
    return None


async def set_cached(
    key: str, value: dict[str, Any], ttl: int = CACHE_TTL_SECONDS
) -> None:
    """Store a value in cache with TTL.

    Args:
        key: The cache key.
        value: The dict to cache (JSON-serializable).
        ttl: Time-to-live in seconds. Defaults to 1 hour.
    """
    try:
        client = await get_redis_client()
        await client.setex(key, ttl, json.dumps(value, default=str))
        logger.debug("Cached key '%s' with TTL %ds", key, ttl)
    except Exception:
        logger.warning("Redis SET failed for key '%s'", key, exc_info=True)


async def invalidate(key: str) -> None:
    """Delete a cached value by key.

    Args:
        key: The cache key to delete.
    """
    try:
        client = await get_redis_client()
        await client.delete(key)
        logger.debug("Invalidated cache key '%s'", key)
    except Exception:
        logger.warning("Redis DELETE failed for key '%s'", key, exc_info=True)


async def close_pool() -> None:
    """Close the Redis connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Redis connection pool closed")
