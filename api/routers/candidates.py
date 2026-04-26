"""Candidate router — profile CRUD, CV upload, saved jobs."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status

from api.dependencies import get_candidate_service, get_current_user, get_job_service
from api.schemas.candidate import (
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
    CVUploadResponse,
)
from api.schemas.common import PaginatedResponse
from api.schemas.job import JobResponse
from api.services.candidate_service import CandidateService
from api.services.job_service import JobService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


@router.get(
    "/profile",
    response_model=CandidateProfileResponse,
    summary="Get current user's candidate profile",
)
def get_profile(
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateProfileResponse:
    """Get the authenticated user's candidate profile.

    Args:
        current_user: Authenticated user from JWT.
        candidate_service: Injected candidate service.

    Returns:
        Candidate profile.
    """
    profile = candidate_service.get_profile(user_id=current_user["id"])
    return CandidateProfileResponse(**profile)


@router.post(
    "/profile",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create candidate profile",
)
def create_profile(
    body: CandidateProfileCreate,
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateProfileResponse:
    """Create a new candidate profile for the authenticated user.

    Args:
        body: Profile creation payload.
        current_user: Authenticated user from JWT.
        candidate_service: Injected candidate service.

    Returns:
        Created candidate profile.
    """
    profile = candidate_service.create_profile(
        user_id=current_user["id"], data=body.model_dump(exclude_unset=True)
    )
    return CandidateProfileResponse(**profile)


@router.put(
    "/profile",
    response_model=CandidateProfileResponse,
    summary="Update candidate profile",
)
def update_profile(
    body: CandidateProfileUpdate,
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CandidateProfileResponse:
    """Update the authenticated user's candidate profile.

    Args:
        body: Profile update payload.
        current_user: Authenticated user from JWT.
        candidate_service: Injected candidate service.

    Returns:
        Updated candidate profile.
    """
    profile = candidate_service.update_profile(
        user_id=current_user["id"], data=body.model_dump(exclude_unset=True)
    )
    return CandidateProfileResponse(**profile)


@router.post(
    "/cv",
    response_model=CVUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload CV document",
)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service),
) -> CVUploadResponse:
    """Upload a CV file (PDF or DOCX) for parsing.

    Args:
        background_tasks: FastAPI background task runner.
        file: Uploaded CV file.
        current_user: Authenticated user from JWT.
        candidate_service: Injected candidate service.

    Returns:
        CV document record with pending status.
    """
    content = await file.read()
    doc = candidate_service.upload_cv(
        user_id=current_user["id"],
        filename=file.filename or "cv.pdf",
        content=content,
        content_type=file.content_type or "",
    )
    background_tasks.add_task(
        candidate_service.parse_cv_background,
        doc_id=doc["id"],
        file_path=doc["file_path"],
        candidate_id=doc["candidate_id"],
    )
    return CVUploadResponse(
        id=doc["id"],
        file_type=doc["file_type"],
        parsing_status=doc["parsing_status"],
        message="CV uploaded successfully. Parsing will start shortly.",
    )


@router.get(
    "/saved-jobs",
    response_model=PaginatedResponse[JobResponse],
    summary="List saved job offers",
)
def list_saved_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> PaginatedResponse[JobResponse]:
    """List saved job offers for the authenticated user.

    Args:
        page: Page number.
        per_page: Results per page.
        current_user: Authenticated user from JWT.
        job_service: Injected job service.

    Returns:
        Paginated list of saved jobs.
    """
    result = job_service.list_saved_jobs(
        user_id=current_user["id"], page=page, per_page=per_page
    )
    return PaginatedResponse[JobResponse](**result)
