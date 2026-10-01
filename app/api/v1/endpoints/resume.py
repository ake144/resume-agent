"""
Legacy resume endpoint.

NOTE: This endpoint is deprecated. Use the new endpoints instead:
- POST /api/v1/applications/generate - for generating applications
- POST /api/v1/jobs/match - for matching jobs
- POST /api/v1/applications/workflow - for full workflow
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_resume_service, get_current_user
from app.core.database import get_db
from app.db.models import ResumeFile, User
from app.schemas.base import APIResponse
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
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: ResumeSerives = Depends(get_resume_service),
    title: str = Form(...),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Ingest resume either from uploaded file or raw text.

    Sent as multipart/form-data (not JSON) so a real file upload can be
    included alongside the other fields. Either `file` or `text` must be
    provided.
    """
    if not file and not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file or text must be provided for ingestion",
        )

    try:
        result = await service.resume_ingest(
            user_id=str(current_user.id), file=file, text=text, title=title, db=db
        )
        return APIResponse(status="success", message="Resume ingested", data=result)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Resume ingestion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest resume",
        )


@router.get(
    "/file",
    summary="Download the resume file on record",
    description="Returns the most recently uploaded PDF resume, if one was uploaded (text-only ingestion has no file to return).",
)
async def get_resume_file(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    resume_file = db.get(ResumeFile, current_user.id)
    if resume_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume file on record - upload a PDF via /resume/ingest first",
        )
    return Response(
        content=resume_file.data,
        media_type=resume_file.content_type,
        headers={"Content-Disposition": f'inline; filename="{resume_file.filename}"'},
    )
