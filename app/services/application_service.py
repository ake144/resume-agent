"""Application service for managing application generation."""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.application import (
    ApplicationGenerationRequest,
    ApplicationGenerationResponse,
    ApplicationType,
    WorkflowRequest
)
from app.agents.generator import generate_application_package
from app.agents.workflow import app_graph
from app.db.models import Application


def _save_application_sync(db: Session, application: Application) -> Application:
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


class ApplicationService(BaseService):
    """Service for application generation operations."""

    async def _persist_application(self, db: Session, application: Application) -> Application:
        # Sync SQLAlchemy call from an async method: threadpooled to avoid
        # blocking the event loop, same pattern used in the ingestion layer.
        return await asyncio.to_thread(_save_application_sync, db, application)

    async def generate_application(
        self,
        request: ApplicationGenerationRequest,
        user_id: str,
        db: Session,
    ) -> ApplicationGenerationResponse:
        """
        Generate an application document (cover letter, resume tailoring, etc.).

        Args:
            request: Application generation request
            user_id: Authenticated user's id
            db: Request-scoped database session

        Returns:
            Generated application response
        """
        try:
            self.log_info(
                "Generating application",
                user_id=user_id,
                job_title=request.job_title,
                type=request.application_type
            )
            result = await generate_application_package(
                user_id=user_id,
                job_description=request.job_description,
                job_title=request.job_title,
                application_type=request.application_type.value,
            )
            self.log_info("Application generated successfully", user_id=user_id)

            application = Application(
                user_id=uuid.UUID(user_id),
                application_type=request.application_type,
                job_title=request.job_title,
                generated_content=result["content"],
                match_score=result["match_score"],
                sources_used=result["sources_used"],
                match_analysis=result.get("match_analysis"),
            )
            await self._persist_application(db, application)

            return ApplicationGenerationResponse(
                user_id=user_id,
                job_title=request.job_title,
                application_type=request.application_type,
                content=result["content"],
                match_score=result["match_score"],
                sources_used=result["sources_used"],
                generated_at=datetime.utcnow().isoformat() + "Z"
            )
        except Exception as e:
            self.log_error(
                f"Failed to generate application: {str(e)}",
                user_id=user_id,
                error=str(e)
            )
            raise

    async def execute_workflow(
        self,
        request: WorkflowRequest,
        user_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Execute the full application workflow.

        Args:
            request: Workflow request
            user_id: Authenticated user's id
            db: Request-scoped database session

        Returns:
            Workflow execution result
        """
        try:
            self.log_info(
                "Executing application workflow",
                user_id=user_id,
                job_title=request.job_title
            )
            initial_state = {
                "user_id": user_id,
                "job_description": request.job_description,
                "job_title": request.job_title
            }
            result = await app_graph.ainvoke(initial_state)
            self.log_info("Workflow executed successfully", user_id=user_id)

            # generate_node in app/agents/workflow.py always generates a cover
            # letter today (hardcoded "cover_letter" application_type).
            final_output = result.get("final_output") or {}
            application = Application(
                user_id=uuid.UUID(user_id),
                application_type=ApplicationType.COVER_LETTER,
                job_title=request.job_title,
                generated_content=result.get("application", ""),
                match_score=final_output.get("match_score"),
                sources_used=final_output.get("sources_used"),
                match_analysis=final_output.get("match_analysis"),
            )
            await self._persist_application(db, application)

            return result
        except Exception as e:
            self.log_error(
                f"Failed to execute workflow: {str(e)}",
                user_id=user_id,
                error=str(e)
            )
            raise
