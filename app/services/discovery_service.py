"""Orchestration for permitted job-source discovery."""
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import JobPosting, JobSource
from app.discovery.providers.greenhouse import DiscoveredJob, fetch_greenhouse_jobs


class DiscoveryService:
    async def discover_source(self, db: Session, user_id: str, source_id: uuid.UUID) -> dict:
        user_uuid = uuid.UUID(user_id)
        source = db.get(JobSource, source_id)
        if source is None or source.user_id != user_uuid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job source not found")
        if not source.enabled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job source is disabled")

        if source.provider.lower() != "greenhouse":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported discovery provider: {source.provider}",
            )

        jobs = await asyncio.to_thread(fetch_greenhouse_jobs, source.source_key)
        now = datetime.now(timezone.utc)
        created = 0
        updated = 0
        for job in jobs:
            existing = (
                db.query(JobPosting)
                .filter(
                    JobPosting.user_id == user_uuid,
                    JobPosting.source_id == source.id,
                    JobPosting.external_id == job.external_id,
                )
                .one_or_none()
            )
            if existing is None:
                db.add(
                    JobPosting(
                        user_id=user_uuid,
                        title=job.title,
                        company=job.company,
                        location=job.location,
                        description=job.description,
                        source_url=job.source_url,
                        source_type=source.provider,
                        source_id=source.id,
                        external_id=job.external_id,
                        discovery_status="discovered",
                        discovered_at=now,
                        expires_at=now + timedelta(days=30),
                    )
                )
                created += 1
            else:
                existing.title = job.title
                existing.company = job.company
                existing.location = job.location
                existing.description = job.description
                existing.source_url = job.source_url
                existing.discovery_status = "discovered"
                existing.discovered_at = now
                existing.expires_at = now + timedelta(days=30)
                updated += 1
        db.commit()
        return {
            "source_id": str(source.id),
            "provider": source.provider,
            "jobs_seen": len(jobs),
            "created": created,
            "updated": updated,
        }
