"""Application generation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.application import (
    ApplicationGenerationRequest,
    ApplicationGenerationResponse,
    WorkflowRequest
)
from app.schemas.base import APIResponse
from app.services.application_service import ApplicationService
from app.api.dependencies import get_application_service
import logging

router = APIRouter(tags=["applications"])
logger = logging.getLogger(__name__)


@router.post(
    "/generate",
    response_model=APIResponse,
    summary="Generate application document",
    description="Generate a cover letter, tailored resume, or interview prep document"
)
async def generate_application(
    request: ApplicationGenerationRequest,
    service: ApplicationService = Depends(get_application_service)
):
    """
    Generate an application document.

    Args:
        request: Application generation request
        service: Application service instance

    Returns:
        API response with generated content

    Raises:
        HTTPException: If generation fails
    """
    try:
        result = await service.generate_application(request)
        return APIResponse(
            status="success",
            message=f"{request.application_type.value.replace('_', ' ').title()} generated successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error generating application: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate application"
        )


@router.post(
    "/workflow",
    response_model=APIResponse,
    summary="Execute full application workflow",
    description="Run the complete workflow: job analysis → matching → application generation"
)
async def execute_workflow(
    request: WorkflowRequest,
    service: ApplicationService = Depends(get_application_service)
):
    """
    Execute the full application workflow.

    Args:
        request: Workflow request with job details
        service: Application service instance

    Returns:
        API response with workflow result

    Raises:
        HTTPException: If workflow fails
    """
    try:
        result = await service.execute_workflow(request)
        return APIResponse(
            status="success",
            message="Workflow executed successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )
