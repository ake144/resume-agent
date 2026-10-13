import asyncio
import uuid
import hashlib
import io
from typing import Any, Dict, Optional

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.db.models import ResumeVersion
from app.services.base import BaseService

MAX_RESUME_FILE_BYTES = 5 * 1024 * 1024  # 5MB


def _upsert_resume_file_sync(db: Session, user_id: uuid.UUID, filename: str, content_type: str, data: bytes):
    from app.db.models import ResumeFile

    existing = db.get(ResumeFile, user_id)
    if existing is not None:
        existing.filename = filename
        existing.content_type = content_type
        existing.data = data
    else:
        db.add(ResumeFile(user_id=user_id, filename=filename, content_type=content_type, data=data))
    db.commit()


def _save_resume_version_sync(
    db: Session,
    user_id: uuid.UUID,
    title: str,
    filename: str | None,
    content_type: str | None,
    data: bytes | None,
    extracted_text: str,
) -> ResumeVersion:
    content_hash = hashlib.sha256(extracted_text.encode("utf-8")).hexdigest()
    existing = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.user_id == user_id, ResumeVersion.content_hash == content_hash)
        .one_or_none()
    )
    if existing is not None:
        return existing

    version = ResumeVersion(
        user_id=user_id,
        title=title,
        filename=filename,
        content_type=content_type,
        data=data,
        extracted_text=extracted_text,
        content_hash=content_hash,
        parser_status="parsed",
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


class ResumeSerives(BaseService):
    """Service for resume-related operations."""

    async def resume_ingest(
        self,
        user_id: str,
        file: Optional[UploadFile],
        text: Optional[str],
        title: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Ingest a resume either from uploaded file or raw text.

        Args:
            user_id: Authenticated user's id
            file: Uploaded resume file, if provided
            text: Raw resume text, if provided (alternative to file)
            title: Resume title
            db: Request-scoped database session

        Returns:
            Ingestion result
        """
        try:
            self.log_info(
                "Ingesting resume",
                user_id=user_id,
                title=title
            )

            # A PDF upload is also persisted as the user's on-file resume
            # (auto-apply needs an actual file to attach to ATS forms - only
            # extracted text survives the ingestion path below). Text-only
            # ingestion never touches this - there's no file to persist.
            if file is not None and file.filename and file.filename.lower().endswith(".pdf"):
                content = await file.read()
                if len(content) > MAX_RESUME_FILE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Resume file exceeds the 5MB limit",
                    )
                await asyncio.to_thread(
                    _upsert_resume_file_sync,
                    db,
                    uuid.UUID(user_id),
                    file.filename,
                    file.content_type or "application/pdf",
                    content,
                )
                # ingest_resume() below does its own independent file.read();
                # reset the stream position rather than re-reading a second
                # UploadFile or threading raw bytes through its signature.
                await file.seek(0)

            version_text = text
            version_data = None
            version_filename = None
            version_content_type = None
            if file is not None and file.filename:
                version_filename = file.filename
                version_content_type = file.content_type or "application/octet-stream"
                await file.seek(0)
                version_data = await file.read()
                if file.filename.lower().endswith(".pdf"):
                    reader = PdfReader(io.BytesIO(version_data))
                    version_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                else:
                    version_text = version_data.decode("utf-8")
                await file.seek(0)

            if version_text and len(version_text.strip()) >= 20:
                await asyncio.to_thread(
                    _save_resume_version_sync,
                    db,
                    uuid.UUID(user_id),
                    title,
                    version_filename,
                    version_content_type,
                    version_data,
                    version_text,
                )

            # Local import to avoid expensive or circular imports at module import time
            from app.ingestion.resume_ingestor import ingest_resume

            result = await ingest_resume(
                user_id=user_id,
                file=file,
                text=text,
                title=title,
            )
            self.log_info(
                "Resume ingested successfully",
                user_id=user_id,
                title=title
            )
            return result
        except Exception as e:
            self.log_error(
                "Error ingesting resume",
                user_id=user_id,
                title=title,
                error=str(e)
            )
            raise