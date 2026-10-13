"""Job service for managing job operations."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.job import (
    JobIngestionRequest,
    JobMatchRequest,
    JobMatchResponse,
    MatchResultDetailResponse,
    MatchResultSummaryResponse,
    JobPostingResponse,
)
from app.ingestion.job_ingestor import ingest_job
from app.agents.matcher import match_job_to_user
from app.db.models import CareerPreference, JobPosting, MatchResult, TargetRole
from fastapi import HTTPException, status


class JobService(BaseService):
    """Service for job-related operations."""

    async def ingest_job(
        self,
        request: JobIngestionRequest,
        user_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Ingest a job posting.

        Args:
            request: Job ingestion request
            user_id: Authenticated user's id
            db: Request-scoped database session

        Returns:
            Ingestion result
        """
        try:
            self.log_info(
                "Ingesting job",
                user_id=user_id,
                title=request.title
            )
            result = await ingest_job(
                db=db,
                user_id=user_id,
                job_text=request.job_text,
                title=request.title,
                source_url=str(request.source_url) if request.source_url else None,
                company=request.company,
                location=request.location,
            )
            self.log_info("Job ingested successfully", user_id=user_id)
            return result
        except Exception as e:
            self.log_error(
                f"Failed to ingest job: {str(e)}",
                user_id=user_id,
                error=str(e)
            )
            raise

    async def match_job(
        self,
        request: JobMatchRequest,
        user_id: str,
        db: Session,
    ) -> JobMatchResponse:
        """
        Match a job with user profile.

        Args:
            request: Job match request
            user_id: Authenticated user's id

        Returns:
            Match analysis and recommendations
        """
        try:
            self.log_info(
                "Matching job",
                user_id=user_id,
                job_title=request.job_title
            )
            user_uuid = uuid.UUID(user_id)
            preferences = db.get(CareerPreference, user_uuid)
            target_roles = (
                db.query(TargetRole)
                .filter(TargetRole.user_id == user_uuid)
                .order_by(TargetRole.priority.asc())
                .all()
            )
            result = await match_job_to_user(
                user_id=user_id,
                job_description=request.job_text,
                job_title=request.job_title,
                preferences={
                    "work_modes": preferences.work_modes if preferences else None,
                    "employment_types": preferences.employment_types if preferences else None,
                    "preferred_locations": preferences.preferred_locations if preferences else None,
                    "minimum_salary": preferences.minimum_salary if preferences else None,
                    "salary_currency": preferences.salary_currency if preferences else None,
                    "willing_to_relocate": preferences.willing_to_relocate if preferences else None,
                    "visa_sponsorship_required": preferences.visa_sponsorship_required if preferences else None,
                },
                target_roles=[role.role_name for role in target_roles],
            )
            if request.job_posting_id is not None:
                posting = db.get(JobPosting, request.job_posting_id)
                if posting is None or posting.user_id != user_uuid:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
                analysis = result["analysis"]
                match_result = MatchResult(
                    user_id=user_uuid,
                    job_posting_id=posting.id,
                    matcher_version="preferences-v1",
                    match_score=analysis.match_score,
                    confidence_level=analysis.confidence_level,
                    preference_alignment=analysis.preference_alignment,
                    strong_matches=analysis.strong_matches,
                    skill_gaps=analysis.skill_gaps,
                    tailoring_recommendations=analysis.tailoring_recommendations,
                    hard_constraints=analysis.hard_constraints,
                    sources=result["sources"],
                )
                db.add(match_result)
                db.commit()
            self.log_info("Job matched successfully", user_id=user_id)
            return result
        except Exception as e:
            self.log_error(
                f"Failed to match job: {str(e)}",
                user_id=user_id,
                error=str(e)
            )
            raise

    def list_match_results(
        self, db: Session, user_id: str, job_posting_id: uuid.UUID | None = None
    ) -> list[MatchResultSummaryResponse]:
        query = db.query(MatchResult).filter(MatchResult.user_id == uuid.UUID(user_id))
        if job_posting_id is not None:
            query = query.filter(MatchResult.job_posting_id == job_posting_id)
        rows = query.order_by(MatchResult.created_at.desc()).limit(50).all()
        return [MatchResultSummaryResponse.model_validate(row) for row in rows]

    def get_match_result(
        self, db: Session, user_id: str, match_id: uuid.UUID
    ) -> MatchResultDetailResponse:
        result = db.get(MatchResult, match_id)
        if result is None or result.user_id != uuid.UUID(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match result not found")
        return MatchResultDetailResponse.model_validate(result)

    def list_job_postings(
        self, db: Session, user_id: str, include_expired: bool = False
    ) -> list[JobPostingResponse]:
        rows = (
            db.query(JobPosting)
            .filter(JobPosting.user_id == uuid.UUID(user_id))
            .order_by(JobPosting.discovered_at.desc())
            .limit(100)
            .all()
        )
        now = datetime.now(timezone.utc)
        results: list[JobPostingResponse] = []
        for posting in rows:
            is_expired = posting.expires_at is not None and posting.expires_at <= now
            if is_expired and not include_expired:
                continue
            latest_match = (
                db.query(MatchResult)
                .filter(
                    MatchResult.user_id == uuid.UUID(user_id),
                    MatchResult.job_posting_id == posting.id,
                )
                .order_by(MatchResult.created_at.desc())
                .first()
            )
            results.append(
                JobPostingResponse(
                    id=posting.id,
                    title=posting.title,
                    company=posting.company,
                    location=posting.location,
                    description=posting.description,
                    source_url=posting.source_url,
                    source_type=posting.source_type,
                    discovered_at=posting.discovered_at,
                    expires_at=posting.expires_at,
                    is_expired=is_expired,
                    latest_match_score=latest_match.match_score if latest_match else None,
                )
            )
        return results
