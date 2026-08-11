"""Shared pytest fixtures: transactional DB session + FastAPI test client.

No separate test database exists for this project (single free-tier
Postgres instance - see the foundation plan's cost constraint), so tests
run against the same database as the app itself. Each test's writes are
isolated via a savepoint-per-test session that's rolled back afterward, so
nothing persists. This is an accepted limitation, not an oversight: these
DB-touching tests need network access to a real reachable Postgres.
"""
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401  (registers tables on Base.metadata for Alembic)
from app.core.database import engine, get_db
from app.core.factory import create_app
from app.core.security import generate_api_key, hash_api_key
from app.db.models import User, UserProfile

_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations():
    """Ensure the schema exists before any test runs. Idempotent - a no-op
    if already at head, which is the common case in local development."""
    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture()
def db_session():
    """A session bound to a per-test savepoint, rolled back after the test.

    Application code's own db.commit() calls only commit to the savepoint,
    not the outer per-test transaction, so nothing written during a test
    persists once that outer transaction is rolled back at teardown.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = _TestSessionLocal(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with get_db overridden to the test's transactional session."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def authed_user(db_session):
    """Create a User (+ its auto-companion UserProfile) directly in the
    test's transactional session. Returns (user, raw_api_key, auth_header).

    Bypasses the real /users registration endpoint since most tests only
    need *an* authenticated user, not to re-test registration itself.
    """
    raw_key = generate_api_key()
    user = User(
        email=f"test-{uuid.uuid4().hex[:12]}@example.com",
        hashed_api_key=hash_api_key(raw_key),
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserProfile(user_id=user.id))
    db_session.flush()

    return user, raw_key, {"Authorization": f"Bearer {raw_key}"}
