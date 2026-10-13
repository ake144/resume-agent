"""Tests for the opportunity inbox and job freshness rules."""
from datetime import datetime, timedelta, timezone

from app.db.models import JobPosting
from app.ingestion.job_ingestor import ingest_job


async def test_duplicate_source_url_is_idempotent(db_session, authed_user):
    user, _, _ = authed_user
    existing = JobPosting(
        user_id=user.id,
        title="Existing role",
        description="Existing description",
        source_url="https://example.com/jobs/1",
        source_type="manual_paste",
    )
    db_session.add(existing)
    db_session.commit()

    result = await ingest_job(
        db=db_session,
        user_id=str(user.id),
        job_text="A duplicate description",
        title="Duplicate role",
        source_url="https://example.com/jobs/1",
    )

    assert result["status"] == "duplicate"
    assert result["job_posting_id"] == str(existing.id)
    assert db_session.query(JobPosting).filter(JobPosting.user_id == user.id).count() == 1


def test_posting_inbox_filters_expired_rows(client, db_session, authed_user):
    user, _, headers = authed_user
    fresh = JobPosting(
        user_id=user.id,
        title="Fresh role",
        description="Fresh description",
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        source_type="manual_paste",
    )
    expired = JobPosting(
        user_id=user.id,
        title="Expired role",
        description="Expired description",
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        source_type="manual_paste",
    )
    db_session.add_all([fresh, expired])
    db_session.commit()

    current = client.get("/api/v1/jobs/postings", headers=headers)
    all_rows = client.get("/api/v1/jobs/postings?include_expired=true", headers=headers)

    assert current.status_code == 200
    assert [row["title"] for row in current.json()["data"]] == ["Fresh role"]
    assert all_rows.status_code == 200
    assert {row["title"] for row in all_rows.json()["data"]} == {"Fresh role", "Expired role"}
