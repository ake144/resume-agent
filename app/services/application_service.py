"""Application service for managing application generation."""
import asyncio
import math
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.application import (
    ApplicationDetailResponse,
    ApplicationGenerationRequest,
    ApplicationGenerationResponse,
    ApplicationListResponse,
    ApplicationType,
    WorkflowRequest
)
from app.agents.generator import generate_application_package
from app.agents.workflow import app_graph
from app.db.models import Application, JobPosting


def _save_application_sync(db: Session, application: Application) -> Application:
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def _resolve_job_posting_sync(
    db: Session, job_posting_id: uuid.UUID | None, user_id: uuid.UUID
) -> JobPosting | None:
    """Look up an owned JobPosting, or 404 if the id is invalid/foreign.

    A client-supplied job_posting_id that doesn't resolve to a posting
    owned by the caller is treated as a client bug worth surfacing, not
    silently dropped - it would otherwise be possible to cross-link
    another user's job posting into this user's application history.
    """
    if job_posting_id is None:
        return None
    posting = db.get(JobPosting, job_posting_id)
    if posting is None or posting.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
    return posting


class ApplicationService(BaseService):
    """Service for application generation operations."""

    async def _persist_application(self, db: Session, application: Application) -> Application:
        # Sync SQLAlchemy call from an async method: threadpooled to avoid
        # blocking the event loop, same pattern used in the ingestion layer.
        return await asyncio.to_thread(_save_application_sync, db, application)

    async def _resolve_job_posting(
        self, db: Session, job_posting_id: uuid.UUID | None, user_id: uuid.UUID
    ) -> JobPosting | None:
        return await asyncio.to_thread(_resolve_job_posting_sync, db, job_posting_id, user_id)

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
            user_uuid = uuid.UUID(user_id)
            job_posting = await self._resolve_job_posting(db, request.job_posting_id, user_uuid)

            result = await generate_application_package(
                user_id=user_id,
                job_description=request.job_description,
                job_title=request.job_title,
                application_type=request.application_type.value,
            )
            self.log_info("Application generated successfully", user_id=user_id)

            application = Application(
                user_id=user_uuid,
                job_posting_id=job_posting.id if job_posting else None,
                application_type=request.application_type,
                job_title=request.job_title,
                company=job_posting.company if job_posting else None,
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
            user_uuid = uuid.UUID(user_id)
            job_posting = await self._resolve_job_posting(db, request.job_posting_id, user_uuid)

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
                user_id=user_uuid,
                job_posting_id=job_posting.id if job_posting else None,
                application_type=ApplicationType.COVER_LETTER,
                job_title=request.job_title,
                company=job_posting.company if job_posting else None,
                generated_content=result.get("application", ""),
                match_score=final_output.get("match_score"),
                sources_used=final_output.get("sources_used"),
                match_analysis=final_output.get("match_analysis"),
            )
            application = await self._persist_application(db, application)
            result["id"] = str(application.id)

            return result
        except Exception as e:
            self.log_error(
                f"Failed to execute workflow: {str(e)}",
                user_id=user_id,
                error=str(e)
            )
            raise

    def list_applications(
        self, db: Session, user_id: str, page: int = 0, size: int = 10
    ) -> ApplicationListResponse:
        """List the authenticated user's applications, newest first."""
        query = db.query(Application).filter(Application.user_id == uuid.UUID(user_id))
        total = query.count()
        rows = (
            query.order_by(Application.created_at.desc())
            .offset(page * size)
            .limit(size)
            .all()
        )
        total_pages = math.ceil(total / size) if size else 0
        return ApplicationListResponse(content=rows, totalItems=total, totalPages=total_pages)

    def get_application(self, db: Session, user_id: str, application_id: uuid.UUID) -> ApplicationDetailResponse:
        """Fetch one application, 404ing if it doesn't exist or isn't owned by the caller."""
        application = db.get(Application, application_id)
        if application is None or application.user_id != uuid.UUID(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        return ApplicationDetailResponse.model_validate(application)
