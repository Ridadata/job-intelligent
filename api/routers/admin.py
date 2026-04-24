"""Admin router — pipeline monitoring, user management, platform stats.

All endpoints require the 'admin' role.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_current_user, get_db, require_role

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_role("admin"))],
)


# ── Pipeline Monitoring ─────────────────────────────────────────────────────


@router.get(
    "/pipeline-runs",
    summary="List recent pipeline runs",
    description="Returns the most recent ETL pipeline runs with status, row counts, and timing.",
)
def list_pipeline_runs(
    limit: int = Query(50, ge=1, le=200, description="Max runs to return"),
    stage: str | None = Query(None, description="Filter by stage (ingest, transform, enrich, etc.)"),
    db=Depends(get_db),
) -> list[dict[str, Any]]:
    """List recent pipeline runs from the pipeline_runs table.

    Args:
        limit: Maximum number of runs to return.
        stage: Optional stage filter.
        db: Supabase client dependency.

    Returns:
        List of pipeline run dicts.
    """
    query = (
        db.table("pipeline_runs")
        .select("id, stage, status, source_name, rows_in, rows_out, rows_skipped, rows_error, duration_ms, error_message, started_at, finished_at")
        .order("started_at", desc=True)
        .limit(limit)
    )
    if stage:
        query = query.eq("stage", stage)

    result = query.execute()
    return result.data or []


# ── User Management ──────────────────────────────────────────────────────────


@router.get(
    "/users",
    summary="List all users",
    description="Returns all registered users with email, role, and status.",
)
def list_users(
    limit: int = Query(100, ge=1, le=500, description="Max users to return"),
    db=Depends(get_db),
) -> list[dict[str, Any]]:
    """List all user accounts.

    Args:
        limit: Maximum number of users to return.
        db: Supabase client dependency.

    Returns:
        List of user dicts (password_hash excluded).
    """
    result = (
        db.table("users")
        .select("id, email, role, is_active, created_at, updated_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


# ── Platform Stats ───────────────────────────────────────────────────────────


@router.get(
    "/stats",
    summary="Platform statistics overview",
    description="Aggregated stats: job counts, user counts, source health, pipeline status.",
)
def platform_stats(db=Depends(get_db)) -> dict[str, Any]:
    """Get platform-wide statistics for the admin dashboard.

    Args:
        db: Supabase client dependency.

    Returns:
        Dict with counts and source breakdown.
    """
    stats: dict[str, Any] = {
        "total_jobs": 0,
        "total_gold_jobs": 0,
        "total_users": 0,
        "total_candidates": 0,
        "total_saved_jobs": 0,
        "sources": [],
        "recent_pipeline": None,
    }

    # Total silver jobs
    try:
        result = db.table("job_offers").select("id", count="exact").execute()
        stats["total_jobs"] = result.count or 0
    except Exception:
        logger.warning("Failed to count job_offers", exc_info=True)

    # Total gold jobs
    try:
        result = db.table("dw_job_offers").select("id", count="exact").execute()
        stats["total_gold_jobs"] = result.count or 0
    except Exception:
        logger.warning("Failed to count dw_job_offers", exc_info=True)

    # Total users
    try:
        result = db.table("users").select("id", count="exact").execute()
        stats["total_users"] = result.count or 0
    except Exception:
        logger.warning("Failed to count users", exc_info=True)

    # Total candidates
    try:
        result = db.table("candidate_profiles").select("id", count="exact").execute()
        stats["total_candidates"] = result.count or 0
    except Exception:
        logger.warning("Failed to count candidate_profiles", exc_info=True)

    # Total saved jobs
    try:
        result = db.table("saved_jobs").select("id", count="exact").execute()
        stats["total_saved_jobs"] = result.count or 0
    except Exception:
        logger.warning("Failed to count saved_jobs", exc_info=True)

    # Source breakdown
    try:
        result = db.table("sources").select("name, base_url, last_scraped_at").execute()
        stats["sources"] = result.data or []
    except Exception:
        logger.warning("Failed to fetch sources", exc_info=True)

    # Most recent pipeline run
    try:
        result = (
            db.table("pipeline_runs")
            .select("stage, status, started_at, duration_ms")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        stats["recent_pipeline"] = result.data[0] if result.data else None
    except Exception:
        logger.warning("Failed to fetch recent pipeline run", exc_info=True)

    return stats
