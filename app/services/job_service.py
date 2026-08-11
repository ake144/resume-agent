"""Job service for managing job operations."""
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.job import JobIngestionRequest, JobMatchRequest, JobMatchResponse
from app.ingestion.job_ingestor import ingest_job
from app.agents.matcher import match_job_to_user


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
            result = await match_job_to_user(
                user_id=user_id,
                job_description=request.job_text,
                job_title=request.job_title
            )
            self.log_info("Job matched successfully", user_id=user_id)
            return result
        except Exception as e:
            self.log_error(
                f"Failed to match job: {str(e)}",
                user_id=user_id,
                error=str(e)
            )
            raise
