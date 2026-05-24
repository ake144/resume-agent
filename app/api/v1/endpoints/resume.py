"""
Legacy resume endpoint.

NOTE: This endpoint is deprecated. Use the new endpoints instead:
- POST /api/v1/applications/generate - for generating applications
- POST /api/v1/jobs/match - for matching jobs
- POST /api/v1/applications/workflow - for full workflow
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_resume_status():
    """
    Check the status of the resume data.

    NOTE: This endpoint is deprecated. See health check endpoint instead.
    """
    return {"message": "Resume endpoint is active.", "deprecated": True}
