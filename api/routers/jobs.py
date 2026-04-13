"""Job router — search, detail, save/unsave endpoints."""

import logging

from fastapi import APIRouter, Depends, Query, status

from api.dependencies import get_current_user, get_job_service
from api.schemas.common import PaginatedResponse
from api.schemas.job import JobResponse
from api.services.job_service import JobService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get(
    "",
    response_model=PaginatedResponse[JobResponse],
    summary="List / search job offers",
)
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    location: str | None = Query(None),
    contract_type: str | None = Query(None),
    skills: str | None = Query(None, description="Comma-separated skill names"),
    salary_min: float | None = Query(None, ge=0),
    salary_max: float | None = Query(None, ge=0),
    job_service: JobService = Depends(get_job_service),
) -> PaginatedResponse[JobResponse]:
    """List job offers with pagination and optional filters.

    Args:
        page: Page number.
        per_page: Results per page.
        q: Free-text search query (matches title, company).
        location: Optional location filter.
        contract_type: Optional contract type filter.
        skills: Comma-separated list of required skills.
        salary_min: Minimum salary filter.
        salary_max: Maximum salary filter.
        job_service: Injected job service.

    Returns:
        Paginated list of jobs.
    """
    skills_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else None
    result = job_service.list_jobs(
        page=page,
        per_page=per_page,
        q=q,
        location=location,
        contract_type=contract_type,
        skills=skills_list,
        salary_min=salary_min,
        salary_max=salary_max,
    )
    return PaginatedResponse[JobResponse](**result)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job offer details",
)
def get_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Get a single job offer by ID.

    Args:
        job_id: Job UUID.
        job_service: Injected job service.

    Returns:
        Job details.
    """
    return JobResponse(**job_service.get_by_id(job_id))


@router.post(
    "/{job_id}/save",
    status_code=status.HTTP_201_CREATED,
    summary="Save a job offer",
)
def save_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> dict:
    """Save a job offer to the user's bookmarks.

    Args:
        job_id: Job UUID to save.
        current_user: Authenticated user.
        job_service: Injected job service.

    Returns:
        Saved job record.
    """
    return job_service.save_job(
        user_id=current_user["id"], job_id=job_id
    )


@router.delete(
    "/{job_id}/save",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unsave a job offer",
)
def unsave_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> None:
    """Remove a job offer from the user's bookmarks.

    Args:
        job_id: Job UUID to unsave.
        current_user: Authenticated user.
        job_service: Injected job service.
    """
    job_service.unsave_job(
        user_id=current_user["id"], job_id=job_id
    )
