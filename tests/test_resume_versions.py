"""Tests for immutable resume version storage and ownership."""
from app.db.models import ResumeVersion
from app.services.resume import _save_resume_version_sync


RESUME_TEXT = "Senior frontend engineer with React, TypeScript, and production application experience."


def test_resume_version_ingestion_is_idempotent(db_session, authed_user):
    user, _, _ = authed_user

    first = _save_resume_version_sync(
        db_session,
        user.id,
        "Primary resume",
        "resume.pdf",
        "application/pdf",
        b"pdf-bytes",
        RESUME_TEXT,
    )
    second = _save_resume_version_sync(
        db_session,
        user.id,
        "Renamed resume",
        "resume-new.pdf",
        "application/pdf",
        b"new-pdf-bytes",
        RESUME_TEXT,
    )

    assert first.id == second.id
    assert db_session.query(ResumeVersion).filter_by(user_id=user.id).count() == 1
    assert second.title == "Primary resume"


def test_resume_version_routes_are_user_scoped(client, db_session, authed_user):
    user, raw_key, headers = authed_user
    version = _save_resume_version_sync(
        db_session,
        user.id,
        "Primary resume",
        "resume.pdf",
        "application/pdf",
        b"pdf-bytes",
        RESUME_TEXT,
    )

    listed = client.get("/api/v1/resume/versions", headers=headers)
    downloaded = client.get(f"/api/v1/resume/versions/{version.id}/file", headers=headers)
    unauthorized = client.get(f"/api/v1/resume/versions/{version.id}/file")

    assert listed.status_code == 200
    assert listed.json()[0]["content_hash"]
    assert downloaded.status_code == 200
    assert downloaded.content == b"pdf-bytes"
    assert unauthorized.status_code in {401, 403}
