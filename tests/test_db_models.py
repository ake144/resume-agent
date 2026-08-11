"""Tests for ORM model constraints: uniqueness, foreign keys, and
cascade/set-null delete behavior.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import generate_api_key, hash_api_key
from app.db.models import Application, JobPosting, User, UserProfile, WorkHistoryEntry
from app.schemas.application import ApplicationType


def _make_user(db_session, email=None):
    user = User(
        email=email or f"test-{uuid.uuid4().hex[:12]}@example.com",
        hashed_api_key=hash_api_key(generate_api_key()),
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_duplicate_email_raises_integrity_error(db_session):
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    _make_user(db_session, email=email)

    with pytest.raises(IntegrityError):
        _make_user(db_session, email=email)


def test_work_history_requires_existing_user(db_session):
    entry = WorkHistoryEntry(
        user_id=uuid.uuid4(),
        company="Acme",
        job_title="Engineer",
        start_date=date(2020, 1, 1),
    )
    db_session.add(entry)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_deleting_user_cascades_to_profile_and_work_history(db_session):
    user = _make_user(db_session)
    db_session.add(UserProfile(user_id=user.id, full_name="Test"))
    db_session.add(
        WorkHistoryEntry(user_id=user.id, company="Acme", job_title="Eng", start_date=date(2020, 1, 1))
    )
    db_session.flush()

    db_session.delete(user)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(UserProfile, user.id) is None
    remaining = db_session.query(WorkHistoryEntry).filter(WorkHistoryEntry.user_id == user.id).all()
    assert remaining == []


def test_deleting_job_posting_sets_application_fk_null(db_session):
    user = _make_user(db_session)
    posting = JobPosting(user_id=user.id, title="Engineer", description="desc")
    db_session.add(posting)
    db_session.flush()

    application = Application(
        user_id=user.id,
        job_posting_id=posting.id,
        application_type=ApplicationType.COVER_LETTER,
        job_title="Engineer",
        generated_content="content",
    )
    db_session.add(application)
    db_session.flush()

    db_session.delete(posting)
    db_session.flush()
    db_session.refresh(application)

    assert application.job_posting_id is None


def test_skill_name_unique_per_user(db_session):
    from app.db.models import SkillEntry

    user = _make_user(db_session)
    db_session.add(SkillEntry(user_id=user.id, name="Python"))
    db_session.flush()

    db_session.add(SkillEntry(user_id=user.id, name="Python"))
    with pytest.raises(IntegrityError):
        db_session.flush()
