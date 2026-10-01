"""Application generation endpoints."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.application import (
    ApplicationDetailResponse,
    ApplicationGenerationRequest,
    ApplicationGenerationResponse,
    ApplicationListResponse,
    WorkflowRequest
)
from app.schemas.base import APIResponse
from app.services.application_service import ApplicationService
from app.api.dependencies import get_application_service, get_current_user
from app.core.database import get_db
from app.db.models import User
import logging

router = APIRouter(tags=["applications"])
logger = logging.getLogger(__name__)
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/generate",
    response_model=APIResponse,
    summary="Generate application document",
    description="Generate a cover letter, tailored resume, or interview prep document"
)
async def generate_application(
    request: ApplicationGenerationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: ApplicationService = Depends(get_application_service)
):
    """
    Generate an application document.

    Args:
        request: Application generation request
        current_user: Authenticated user (derived from the API key)
        db: Request-scoped database session
        service: Application service instance

    Returns:
        API response with generated content

    Raises:
        HTTPException: If generation fails
    """
    try:
        result = await service.generate_application(request, user_id=str(current_user.id), db=db)
        return APIResponse(
            status="success",
            message=f"{request.application_type.value.replace('_', ' ').title()} generated successfully",
            data=result
        )
    except HTTPException:
        raise
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
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    service: ApplicationService = Depends(get_application_service)
):
    """
    Execute the full application workflow.

    Args:
        request: Workflow request with job details
        current_user: Authenticated user (derived from the API key)
        db: Request-scoped database session
        service: Application service instance

    Returns:
        API response with workflow result

    Raises:
        HTTPException: If workflow fails
    """
    try:
        result = await service.execute_workflow(request, user_id=str(current_user.id), db=db)
        return APIResponse(
            status="success",
            message="Workflow executed successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )


@router.get(
    "",
    response_model=APIResponse,
    summary="List your applications",
    description="Paginated list of the authenticated user's applications, newest first",
)
def list_applications(
    current_user: CurrentUser,
    db: DbSession,
    page: int = 0,
    size: int = 10,
    service: ApplicationService = Depends(get_application_service),
):
    result = service.list_applications(db, user_id=str(current_user.id), page=page, size=size)
    return APIResponse(status="success", message="Applications retrieved", data=result)


@router.get(
    "/{application_id}",
    response_model=APIResponse,
    summary="Get one application",
    description="Fetch a single application by id, including its generated content and match analysis",
)
def get_application(
    application_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    service: ApplicationService = Depends(get_application_service),
):
    result = service.get_application(db, user_id=str(current_user.id), application_id=application_id)
    return APIResponse(status="success", message="Application retrieved", data=result)
