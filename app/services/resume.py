from typing import Any, Dict

from app.schemas.resume import ResumeIngestionRequest
from app.services.base import BaseService


class ResumeSerives(BaseService):
    """Service for resume-related operations."""

    async def resume_ingest(
        self,
        request: ResumeIngestionRequest
    ) -> Dict[str, Any]:
        """
        Ingest a resume either from uploaded file or raw text.

        Args:
            request: Resume ingestion request containing file or text
    
        Returns:
            Ingestion result
        """
        try:
            self.log_info(
                "Ingesting resume",
                user_id=request.user_id,
                title=request.title
            )

            # Local import to avoid expensive or circular imports at module import time
            from app.ingestion.resume_ingestor import ingest_resume

            # Pass explicit fields from the request into the ingestor
            result = await ingest_resume(
                user_id=request.user_id,
                file=getattr(request, "file", None),
                text=getattr(request, "text", None),
                title=getattr(request, "title", "My Resume"),
            )
            self.log_info(
                "Resume ingested successfully",
                user_id=request.user_id,
                title=request.title
            )
            return result
        except Exception as e:
            self.log_error(
                "Error ingesting resume",
                user_id=request.user_id,
                title=request.title,
                error=str(e)
            )
            raise