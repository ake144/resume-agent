"""Job-related endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.job import JobIngestionRequest, JobMatchRequest, JobMatchResponse
from app.schemas.base import APIResponse
from app.services.job_service import JobService
from app.api.dependencies import get_job_service
import logging

router = APIRouter(tags=["jobs"])
logger = logging.getLogger(__name__)


@router.post(
    "/ingest",
    response_model=APIResponse,
    summary="Ingest a job posting",
    description="Ingest and store a job posting for later analysis"
)
async def ingest_job(
    request: JobIngestionRequest,
    service: JobService = Depends(get_job_service)
):
    """
    Ingest a new job posting.

    Args:
        request: Job ingestion request with job details
        service: Job service instance

    Returns:
        API response with ingestion result

    Raises:
        HTTPException: If ingestion fails
    """
    try:
        result = await service.ingest_job(request)
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
    service: JobService = Depends(get_job_service)
):
    """
    Match a job with user's profile.

    Args:
        request: Job match request with user and job details
        service: Job service instance

    Returns:
        API response with match analysis

    Raises:
        HTTPException: If matching fails
    """
    try:
        result = await service.match_job(request)
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
