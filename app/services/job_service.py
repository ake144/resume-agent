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
    JobSourceCreate,
    JobSourceResponse,
    RankJobPostingsRequest,
    RankJobPostingsResponse,
)
from app.ingestion.job_ingestor import ingest_job
from app.agents.matcher import match_job_to_user
from app.db.models import CareerPreference, JobPosting, JobSource, MatchResult, ResumeVersion, TargetRole
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
            source_id = request.source_id
            if source_id is not None:
                source = db.get(JobSource, source_id)
                if source is None or source.user_id != uuid.UUID(user_id) or not source.enabled:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job source not found")
            result = await ingest_job(
                db=db,
                user_id=user_id,
                job_text=request.job_text,
                title=request.title,
                source_url=str(request.source_url) if request.source_url else None,
                company=request.company,
                location=request.location,
                source_type=request.source_type,
                source_id=source_id,
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
            preferences, target_roles = self._matching_context(db, user_uuid)
            result = await self._evaluate_job(
                user_id=user_id,
                job_description=request.job_text,
                job_title=request.job_title,
                preferences=preferences,
                target_roles=target_roles,
            )
            if request.job_posting_id is not None:
                posting = db.get(JobPosting, request.job_posting_id)
                if posting is None or posting.user_id != user_uuid:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job posting not found")
                self._save_match(db, user_uuid, posting.id, result)
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

    @staticmethod
    def _matching_context(db: Session, user_id: uuid.UUID) -> tuple[dict, list[str]]:
        preferences = db.get(CareerPreference, user_id)
        roles = (
            db.query(TargetRole)
            .filter(TargetRole.user_id == user_id)
            .order_by(TargetRole.priority.asc())
            .all()
        )
        return (
            {
                "work_modes": preferences.work_modes if preferences else None,
                "employment_types": preferences.employment_types if preferences else None,
                "preferred_locations": preferences.preferred_locations if preferences else None,
                "minimum_salary": preferences.minimum_salary if preferences else None,
                "salary_currency": preferences.salary_currency if preferences else None,
                "willing_to_relocate": preferences.willing_to_relocate if preferences else None,
                "visa_sponsorship_required": preferences.visa_sponsorship_required if preferences else None,
            },
            [role.role_name for role in roles],
        )

    @staticmethod
    async def _evaluate_job(
        *, user_id: str, job_description: str, job_title: str, preferences: dict, target_roles: list[str]
    ) -> dict:
        return await match_job_to_user(
            user_id=user_id,
            job_description=job_description,
            job_title=job_title,
            preferences=preferences,
            target_roles=target_roles,
        )

    @staticmethod
    def _save_match(db: Session, user_id: uuid.UUID, posting_id: uuid.UUID, result: dict) -> MatchResult:
        analysis = result["analysis"]
        resume_version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.user_id == user_id)
            .order_by(ResumeVersion.created_at.desc())
            .first()
        )
        match_result = MatchResult(
            user_id=user_id,
            job_posting_id=posting_id,
            resume_version_id=resume_version.id if resume_version else None,
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
        return match_result

    async def rank_job_postings(
        self, db: Session, user_id: str, request: RankJobPostingsRequest
    ) -> RankJobPostingsResponse:
        """Evaluate active owned postings and persist an immutable match snapshot.

        By default, already-ranked rows are skipped.  A caller can explicitly
        request a refresh after a source updates a posting or profile material.
        """
        user_uuid = uuid.UUID(user_id)
        now = datetime.now(timezone.utc)
        query = db.query(JobPosting).filter(JobPosting.user_id == user_uuid).filter(
            (JobPosting.expires_at.is_(None)) | (JobPosting.expires_at > now)
        )
        if request.posting_ids is not None:
            query = query.filter(JobPosting.id.in_(request.posting_ids))
        if request.source_id is not None:
            query = query.filter(JobPosting.source_id == request.source_id)
        postings = query.order_by(JobPosting.discovered_at.desc()).limit(request.limit).all()
        preferences, target_roles = self._matching_context(db, user_uuid)
        match_ids: list[uuid.UUID] = []
        skipped = failed = 0
        for posting in postings:
            has_match = db.query(MatchResult.id).filter(
                MatchResult.user_id == user_uuid, MatchResult.job_posting_id == posting.id
            ).first()
            if has_match and not request.refresh:
                skipped += 1
                continue
            try:
                result = await self._evaluate_job(
                    user_id=user_id,
                    job_description=posting.description,
                    job_title=posting.title,
                    preferences=preferences,
                    target_roles=target_roles,
                )
                saved = self._save_match(db, user_uuid, posting.id, result)
                db.flush()
                match_ids.append(saved.id)
            except Exception as error:
                self.log_error("Could not rank discovered opportunity", posting_id=str(posting.id), error=str(error))
                failed += 1
        db.commit()
        return RankJobPostingsResponse(
            evaluated=len(match_ids), skipped=skipped, failed=failed, match_ids=match_ids
        )

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
                    source_id=posting.source_id,
                    discovery_status=posting.discovery_status,
                    discovered_at=posting.discovered_at,
                    expires_at=posting.expires_at,
                    is_expired=is_expired,
                    latest_match_score=latest_match.match_score if latest_match else None,
                )
            )
        return sorted(
            results,
            key=lambda posting: (
                posting.latest_match_score is None,
                -(posting.latest_match_score or 0),
                -posting.discovered_at.timestamp(),
            ),
        )

    def list_job_sources(self, db: Session, user_id: str) -> list[JobSourceResponse]:
        rows = (
            db.query(JobSource)
            .filter(JobSource.user_id == uuid.UUID(user_id))
            .order_by(JobSource.provider.asc(), JobSource.source_key.asc())
            .all()
        )
        return [JobSourceResponse.model_validate(row) for row in rows]

    def create_job_source(
        self, db: Session, user_id: str, data: JobSourceCreate
    ) -> JobSourceResponse:
        source = JobSource(user_id=uuid.UUID(user_id), **data.model_dump())
        db.add(source)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job source already exists")
        db.refresh(source)
        return JobSourceResponse.model_validate(source)
