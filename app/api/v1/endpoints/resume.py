"""
Legacy resume endpoint.

NOTE: This endpoint is deprecated. Use the new endpoints instead:
- POST /api/v1/applications/generate - for generating applications
- POST /api/v1/jobs/match - for matching jobs
- POST /api/v1/applications/workflow - for full workflow
"""
from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from app.api.dependencies import get_resume_service
from app.schemas.base import APIResponse
from app.schemas.resume import ResumeIngestionRequest
from app.services.resume import ResumeSerives
import logging


router = APIRouter(tags=["resume"])
logger = logging.getLogger(__name__)


@router.get("/")
async def get_resume_status():
    """
    Check the status of the resume data.

    NOTE: This endpoint is deprecated. See health check endpoint instead.
    """
    return {"message": "Resume endpoint is active.", "deprecated": True}


@router.post(
    "/ingest",
    response_model=APIResponse,
    summary="Ingest a resume",
    description="Upload a resume file or provide resume text to ingest into the knowledge base"
)
async def post_ingest_resume(
    request: ResumeIngestionRequest,
    service: ResumeSerives = Depends(get_resume_service),
):
    """Ingest resume either from uploaded file or raw text.

    Either `file` or `text` must be provided.
    """
    if not request.file and not request.text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file or text must be provided for ingestion",
        )

    try:
        result = await service.resume_ingest(request)
        return APIResponse(status="success", message="Resume ingested", data=result)
    except Exception:
        logger.exception("Resume ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest resume",
        )
