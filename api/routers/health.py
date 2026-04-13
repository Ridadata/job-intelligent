"""Health and readiness check endpoints."""

import logging

from fastapi import APIRouter, Depends

from api.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness check")
def health() -> dict:
    """Basic liveness check for Docker and load balancers.

    Returns:
        Status dict.
    """
    return {"status": "healthy"}


@router.get("/readiness", summary="Readiness check (DB + Redis)")
async def readiness(db=Depends(get_db)) -> dict:
    """Deep readiness check — verifies DB and Redis connectivity.

    Args:
        db: Supabase client.

    Returns:
        Status dict with component health.
    """
    checks: dict = {"database": False, "redis": False}

    # Check database
    try:
        db.table("sources").select("id").limit(1).execute()
        checks["database"] = True
    except Exception as exc:
        logger.warning("Readiness: DB check failed: %s", exc)

    # Check Redis
    try:
        import redis.asyncio as aioredis
        from api.config import api_settings

        r = aioredis.from_url(api_settings.redis_url, decode_responses=True)
        await r.ping()
        checks["redis"] = True
        await r.aclose()
    except Exception as exc:
        logger.warning("Readiness: Redis check failed: %s", exc)

    all_ok = all(checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}
