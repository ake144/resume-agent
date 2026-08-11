"""Tests for the API-key auth dependency."""
import uuid

from app.core.security import generate_api_key, hash_api_key
from app.db.models import User


def test_missing_key_returns_401(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_garbage_key_returns_401(client):
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-key"})
    assert response.status_code == 401


def test_inactive_user_key_returns_401(client, db_session):
    raw_key = generate_api_key()
    user = User(
        email=f"inactive-{uuid.uuid4().hex[:8]}@example.com",
        hashed_api_key=hash_api_key(raw_key),
        is_active=False,
    )
    db_session.add(user)
    db_session.flush()

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {raw_key}"})
    assert response.status_code == 401


def test_valid_key_resolves_correct_user(client, authed_user):
    user, _, headers = authed_user
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)


def test_hash_api_key_is_deterministic():
    raw_key = generate_api_key()
    assert hash_api_key(raw_key) == hash_api_key(raw_key)


def test_different_keys_hash_differently():
    assert hash_api_key(generate_api_key()) != hash_api_key(generate_api_key())
