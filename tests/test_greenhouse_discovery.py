"""Tests for the permitted Greenhouse discovery adapter."""
from unittest.mock import patch

from app.db.models import JobPosting, JobSource
from app.discovery.providers.greenhouse import DiscoveredJob, strip_html
from app.services.discovery_service import DiscoveryService


def test_strip_html_returns_readable_job_text():
    assert strip_html("<p>Build <strong>React</strong> products.</p>") == "Build React products."


async def test_discovery_upserts_jobs_for_owned_source(db_session, authed_user):
    user, _, _ = authed_user
    source = JobSource(user_id=user.id, provider="greenhouse", source_key="example", enabled=True)
    db_session.add(source)
    db_session.commit()

    jobs = [
        DiscoveredJob(
            external_id="123",
            title="Frontend Engineer",
            description="Build React products.",
            company="Example",
            location="Remote",
            source_url="https://boards.greenhouse.io/example/jobs/123",
        )
    ]
    with patch("app.services.discovery_service.fetch_greenhouse_jobs", return_value=jobs):
        result = await DiscoveryService().discover_source(db_session, str(user.id), source.id)

    assert result["created"] == 1
    assert db_session.query(JobPosting).filter(JobPosting.source_id == source.id).count() == 1

    with patch("app.services.discovery_service.fetch_greenhouse_jobs", return_value=jobs):
        result = await DiscoveryService().discover_source(db_session, str(user.id), source.id)

    assert result["created"] == 0
    assert result["updated"] == 1
    assert db_session.query(JobPosting).filter(JobPosting.source_id == source.id).count() == 1
