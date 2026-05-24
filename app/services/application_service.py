"""Application service for managing application generation."""
from typing import Dict, Any
from app.services.base import BaseService
from app.schemas.application import (
    ApplicationGenerationRequest,
    ApplicationGenerationResponse,
    WorkflowRequest
)
from app.agents.generator import generate_application_package
from app.agents.workflow import app_graph
from datetime import datetime


class ApplicationService(BaseService):
    """Service for application generation operations."""

    async def generate_application(
        self,
        request: ApplicationGenerationRequest
    ) -> ApplicationGenerationResponse:
        """
        Generate an application document (cover letter, resume tailoring, etc.).

        Args:
            request: Application generation request

        Returns:
            Generated application response
        """
        try:
            self.log_info(
                "Generating application",
                user_id=request.user_id,
                job_title=request.job_title,
                type=request.application_type
            )
            content = await generate_application_package(
                user_id=request.user_id,
                job_description=request.job_description,
                job_title=request.job_title,
                type=request.application_type.value
            )
            self.log_info("Application generated successfully", user_id=request.user_id)
            return ApplicationGenerationResponse(
                user_id=request.user_id,
                job_title=request.job_title,
                application_type=request.application_type,
                content=content,
                generated_at=datetime.utcnow().isoformat() + "Z"
            )
        except Exception as e:
            self.log_error(
                f"Failed to generate application: {str(e)}",
                user_id=request.user_id,
                error=str(e)
            )
            raise

    async def execute_workflow(
        self,
        request: WorkflowRequest
    ) -> Dict[str, Any]:
        """
        Execute the full application workflow.

        Args:
            request: Workflow request

        Returns:
            Workflow execution result
        """
        try:
            self.log_info(
                "Executing application workflow",
                user_id=request.user_id,
                job_title=request.job_title
            )
            initial_state = {
                "user_id": request.user_id,
                "job_description": request.job_description,
                "job_title": request.job_title
            }
            result = await app_graph.ainvoke(initial_state)
            self.log_info("Workflow executed successfully", user_id=request.user_id)
            return result
        except Exception as e:
            self.log_error(
                f"Failed to execute workflow: {str(e)}",
                user_id=request.user_id,
                error=str(e)
            )
            raise
