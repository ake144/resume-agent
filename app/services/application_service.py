"""Application service for managing application generation."""
import asyncio
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.application import (
    ApplicationDetailResponse,
    ApplicationGenerationRequest,
    ApplicationGenerationResponse,
    ApplicationListResponse,
    ApplicationArtifactResponse,
    ArtifactReviewRequest,
    ArtifactRevisionRequest,
    ApplicationStatusUpdateRequest, ApplicationEventResponse,
    ApplicationTaskCreate, ApplicationTaskResponse,
    ApplicationContactCreate, ApplicationContactResponse,
    ApplicationType,
    WorkflowRequest
)
from app.agents.generator import generate_application_package
from app.agents.workflow import app_graph
from app.db.models import Application, ApplicationArtifact, ApplicationContact, ApplicationEvent, ApplicationTask, JobPosting


def _save_application_sync(db: Session, application: Application) -> Application:
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def _save_artifact_sync(db: Session, artifact: ApplicationArtifact) -> ApplicationArtifact:
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


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

    async def _persist_artifact(self, db: Session, artifact: ApplicationArtifact) -> ApplicationArtifact:
        return await asyncio.to_thread(_save_artifact_sync, db, artifact)

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
            application = await self._persist_application(db, application)
            artifact = ApplicationArtifact(
                user_id=user_uuid, application_id=application.id,
                artifact_type=request.application_type.value, state="needs_review",
                content=result["content"], evidence_citations=result.get("evidence_citations", []),
                unsupported_claims=result.get("unsupported_claims", []),
            )
            artifact = await self._persist_artifact(db, artifact)

            return ApplicationGenerationResponse(
                user_id=user_id,
                job_title=request.job_title,
                application_type=request.application_type,
                content=result["content"],
                match_score=result["match_score"],
                sources_used=result["sources_used"],
                generated_at=datetime.now(timezone.utc).isoformat(),
                artifact_id=artifact.id,
                artifact_state="needs_review",
                evidence_citations=artifact.evidence_citations,
                unsupported_claims=artifact.unsupported_claims,
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
            artifact = ApplicationArtifact(
                user_id=user_uuid, application_id=application.id,
                artifact_type=ApplicationType.COVER_LETTER.value, state="needs_review",
                content=application.generated_content,
                evidence_citations=final_output.get("evidence_citations", []),
                unsupported_claims=final_output.get("unsupported_claims", []),
            )
            await self._persist_artifact(db, artifact)
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
        self, db: Session, user_id: str, page: int = 0, size: int = 10,
        status_filter: ApplicationStatus | None = None, sort: str = "newest",
    ) -> ApplicationListResponse:
        """List the authenticated user's applications, newest first."""
        query = db.query(Application).filter(Application.user_id == uuid.UUID(user_id))
        if status_filter is not None:
            query = query.filter(Application.status == status_filter)
        total = query.count()
        ordering = Application.created_at.desc() if sort == "newest" else Application.created_at.asc()
        rows = (
            query.order_by(ordering, Application.id.desc())
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

    def list_artifacts(self, db: Session, user_id: str, application_id: uuid.UUID) -> list[ApplicationArtifactResponse]:
        self.get_application(db, user_id, application_id)
        rows = db.query(ApplicationArtifact).filter(
            ApplicationArtifact.application_id == application_id,
            ApplicationArtifact.user_id == uuid.UUID(user_id),
        ).order_by(ApplicationArtifact.created_at.desc()).all()
        return [ApplicationArtifactResponse.model_validate(row) for row in rows]

    def _get_owned_artifact(self, db: Session, user_id: str, artifact_id: uuid.UUID) -> ApplicationArtifact:
        artifact = db.get(ApplicationArtifact, artifact_id)
        if artifact is None or artifact.user_id != uuid.UUID(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application artifact not found")
        return artifact

    def approve_artifact(self, db: Session, user_id: str, artifact_id: uuid.UUID, request: ArtifactReviewRequest) -> ApplicationArtifactResponse:
        artifact = self._get_owned_artifact(db, user_id, artifact_id)
        if artifact.state != "needs_review":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only artifacts awaiting review can be approved")
        artifact.state, artifact.review_notes, artifact.reviewed_at = "approved", request.review_notes, datetime.now(timezone.utc)
        db.commit(); db.refresh(artifact)
        return ApplicationArtifactResponse.model_validate(artifact)

    def reject_artifact(self, db: Session, user_id: str, artifact_id: uuid.UUID, request: ArtifactReviewRequest) -> ApplicationArtifactResponse:
        artifact = self._get_owned_artifact(db, user_id, artifact_id)
        if artifact.state != "needs_review":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only artifacts awaiting review can be rejected")
        artifact.state, artifact.review_notes, artifact.reviewed_at = "rejected", request.review_notes, datetime.now(timezone.utc)
        db.commit(); db.refresh(artifact)
        return ApplicationArtifactResponse.model_validate(artifact)

    def revise_artifact(self, db: Session, user_id: str, artifact_id: uuid.UUID, request: ArtifactRevisionRequest) -> ApplicationArtifactResponse:
        artifact = self._get_owned_artifact(db, user_id, artifact_id)
        if artifact.state not in {"needs_review", "rejected"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only unapproved artifacts can be revised")
        artifact.state, artifact.reviewed_at = "revised", datetime.now(timezone.utc)
        revised = ApplicationArtifact(
            user_id=artifact.user_id, application_id=artifact.application_id, parent_artifact_id=artifact.id,
            artifact_type=artifact.artifact_type, state="needs_review", content=request.content,
            evidence_citations=artifact.evidence_citations, unsupported_claims=artifact.unsupported_claims,
            review_notes=request.review_notes,
        )
        db.add(revised); db.commit(); db.refresh(revised)
        return ApplicationArtifactResponse.model_validate(revised)

    def update_status(self, db: Session, user_id: str, application_id: uuid.UUID, request: ApplicationStatusUpdateRequest) -> ApplicationDetailResponse:
        application = db.get(Application, application_id)
        if application is None or application.user_id != uuid.UUID(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        transitions = {
            "draft": {"generated", "withdrawn"}, "generated": {"submitted", "withdrawn"},
            "submitted": {"interviewing", "rejected", "withdrawn", "offer"},
            "interviewing": {"offer", "rejected", "withdrawn"}, "offer": {"withdrawn"},
            "rejected": set(), "withdrawn": set(),
        }
        old, new = application.status.value, request.status.value
        if new not in transitions[old]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot change {old} to {new}")
        application.status = request.status
        if new == "submitted": application.submitted_at = datetime.now(timezone.utc)
        db.add(ApplicationEvent(user_id=application.user_id, application_id=application.id, event_type="status_changed", from_status=old, to_status=new, note=request.note))
        db.commit(); db.refresh(application)
        return ApplicationDetailResponse.model_validate(application)

    def list_events(self, db: Session, user_id: str, application_id: uuid.UUID) -> list[ApplicationEventResponse]:
        self.get_application(db, user_id, application_id)
        rows = db.query(ApplicationEvent).filter(ApplicationEvent.application_id == application_id, ApplicationEvent.user_id == uuid.UUID(user_id)).order_by(ApplicationEvent.created_at.desc()).all()
        return [ApplicationEventResponse.model_validate(row) for row in rows]

    def create_task(self, db: Session, user_id: str, application_id: uuid.UUID, request: ApplicationTaskCreate) -> ApplicationTaskResponse:
        application = self.get_application(db, user_id, application_id)
        task = ApplicationTask(user_id=uuid.UUID(user_id), application_id=application.id, **request.model_dump())
        db.add(task); db.commit(); db.refresh(task)
        return ApplicationTaskResponse.model_validate(task)

    def list_tasks(self, db: Session, user_id: str, application_id: uuid.UUID) -> list[ApplicationTaskResponse]:
        self.get_application(db, user_id, application_id)
        rows = db.query(ApplicationTask).filter(ApplicationTask.user_id == uuid.UUID(user_id), ApplicationTask.application_id == application_id).order_by(ApplicationTask.due_at.asc().nullslast(), ApplicationTask.created_at.desc()).all()
        return [ApplicationTaskResponse.model_validate(row) for row in rows]

    def complete_task(self, db: Session, user_id: str, task_id: uuid.UUID) -> ApplicationTaskResponse:
        task = db.get(ApplicationTask, task_id)
        if task is None or task.user_id != uuid.UUID(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
        if task.completed_at is None:
            task.completed_at = datetime.now(timezone.utc)
            db.add(ApplicationEvent(user_id=task.user_id, application_id=task.application_id, event_type="task_completed", note=task.title))
            db.commit(); db.refresh(task)
        return ApplicationTaskResponse.model_validate(task)

    def create_contact(self, db: Session, user_id: str, application_id: uuid.UUID, request: ApplicationContactCreate) -> ApplicationContactResponse:
        application = self.get_application(db, user_id, application_id)
        contact = ApplicationContact(user_id=uuid.UUID(user_id), application_id=application.id, **request.model_dump())
        db.add(contact); db.commit(); db.refresh(contact)
        return ApplicationContactResponse.model_validate(contact)

    def list_contacts(self, db: Session, user_id: str, application_id: uuid.UUID) -> list[ApplicationContactResponse]:
        self.get_application(db, user_id, application_id)
        rows = db.query(ApplicationContact).filter(ApplicationContact.user_id == uuid.UUID(user_id), ApplicationContact.application_id == application_id).order_by(ApplicationContact.created_at.desc()).all()
        return [ApplicationContactResponse.model_validate(row) for row in rows]
