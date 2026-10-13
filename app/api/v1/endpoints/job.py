"""Job-related endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.job import (
    JobIngestionRequest,
    JobMatchRequest,
    JobMatchResponse,
    JobSourceCreate,
    LocalSourcePresetResponse,
)
from uuid import UUID
from app.schemas.base import APIResponse
from app.services.job_service import JobService
from app.services.discovery_service import DiscoveryService
from app.discovery.local_sources import list_source_presets
from app.api.dependencies import get_job_service, get_current_user
from app.core.database import get_db
from app.db.models import User
import logging

router = APIRouter(tags=["jobs"])
logger = logging.getLogger(__name__)


@router.get(
    "/local-sources",
    response_model=list[LocalSourcePresetResponse],
    summary="List local and international job source presets",
)
def list_local_sources():
    return list_source_presets()


@router.post(
    "/ingest",
    response_model=APIResponse,
    summary="Ingest a job posting",
    description="Ingest and store a job posting for later analysis"
)
async def ingest_job(
    request: JobIngestionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: JobService = Depends(get_job_service)
):
    """
    Ingest a new job posting.

    Args:
        request: Job ingestion request with job details
        current_user: Authenticated user (derived from the API key)
        db: Request-scoped database session
        service: Job service instance

    Returns:
        API response with ingestion result

    Raises:
        HTTPException: If ingestion fails
    """
    try:
        result = await service.ingest_job(request, user_id=str(current_user.id), db=db)
        return APIResponse(
            status="success",
            message="Job ingested successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error ingesting job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest job"
        )


@router.post(
    "/match",
    response_model=APIResponse,
    summary="Match job with user profile",
    description="Analyze how well a job matches with a user's profile"
)
async def match_job(
    request: JobMatchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: JobService = Depends(get_job_service)
):
    """
    Match a job with user's profile.

    Args:
        request: Job match request with job details
        current_user: Authenticated user (derived from the API key)
        service: Job service instance

    Returns:
        API response with match analysis

    Raises:
        HTTPException: If matching fails
    """
    try:
        result = await service.match_job(request, user_id=str(current_user.id), db=db)
        return APIResponse(
            status="success",
            message="Job matched successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error matching job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to match job"
        )


@router.get(
    "/matches",
    response_model=APIResponse,
    summary="List saved job matches",
)
def list_matches(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    job_posting_id: UUID | None = None,
    service: JobService = Depends(get_job_service),
):
    result = service.list_match_results(db, str(current_user.id), job_posting_id)
    return APIResponse(status="success", message="Matches retrieved", data=result)


@router.get(
    "/postings",
    response_model=APIResponse,
    summary="List stored job opportunities",
)
def list_postings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    include_expired: bool = False,
    service: JobService = Depends(get_job_service),
):
    result = service.list_job_postings(db, str(current_user.id), include_expired)
    return APIResponse(status="success", message="Job postings retrieved", data=result)


@router.get(
    "/sources",
    response_model=APIResponse,
    summary="List configured job sources",
)
def list_sources(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: JobService = Depends(get_job_service),
):
    result = service.list_job_sources(db, str(current_user.id))
    return APIResponse(status="success", message="Job sources retrieved", data=result)


@router.post(
    "/sources",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure a job source",
)
def create_source(
    request: JobSourceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: JobService = Depends(get_job_service),
):
    result = service.create_job_source(db, str(current_user.id), request)
    return APIResponse(status="success", message="Job source configured", data=result)


@router.post(
    "/sources/{source_id}/discover",
    response_model=APIResponse,
    summary="Discover jobs from a configured source",
)
async def discover_source(
    source_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: DiscoveryService = Depends(DiscoveryService),
):
    result = await service.discover_source(db, str(current_user.id), source_id)
    return APIResponse(status="success", message="Job discovery completed", data=result)


@router.get(
    "/matches/{match_id}",
    response_model=APIResponse,
    summary="Get a saved job match",
)
def get_match(
    match_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: JobService = Depends(get_job_service),
):
    result = service.get_match_result(db, str(current_user.id), match_id)
    return APIResponse(status="success", message="Match retrieved", data=result)
