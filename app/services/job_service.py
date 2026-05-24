"""Job service for managing job operations."""
from typing import Dict, Any, Optional
from app.services.base import BaseService
from app.schemas.job import JobIngestionRequest, JobMatchRequest, JobMatchResponse
from app.ingestion.job_ingestor import ingest_job
from app.agents.matcher import match_job_to_user


class JobService(BaseService):
    """Service for job-related operations."""

    async def ingest_job(
        self,
        request: JobIngestionRequest
    ) -> Dict[str, Any]:
        """
        Ingest a job posting.

        Args:
            request: Job ingestion request

        Returns:
            Ingestion result
        """
        try:
            self.log_info(
                "Ingesting job",
                user_id=request.user_id,
                title=request.title
            )
            result = await ingest_job(
                user_id=request.user_id,
                job_text=request.job_text,
                title=request.title,
                source_url=str(request.source_url) if request.source_url else None
            )
            self.log_info("Job ingested successfully", user_id=request.user_id)
            return result
        except Exception as e:
            self.log_error(
                f"Failed to ingest job: {str(e)}",
                user_id=request.user_id,
                error=str(e)
            )
            raise

    async def match_job(
        self,
        request: JobMatchRequest
    ) -> JobMatchResponse:
        """
        Match a job with user profile.

        Args:
            request: Job match request

        Returns:
            Match analysis and recommendations
        """
        try:
            self.log_info(
                "Matching job",
                user_id=request.user_id,
                job_title=request.job_title
            )
            result = await match_job_to_user(
                user_id=request.user_id,
                job_text=request.job_text,
                job_title=request.job_title
            )
            self.log_info("Job matched successfully", user_id=request.user_id)
            return result
        except Exception as e:
            self.log_error(
                f"Failed to match job: {str(e)}",
                user_id=request.user_id,
                error=str(e)
            )
            raise
