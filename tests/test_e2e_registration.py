"""End-to-end test: register a real account over HTTP, then use the
returned API key against a protected endpoint.
"""
import uuid

from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.factory import create_app


async def test_register_then_access_protected_endpoint(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = f"e2e-{uuid.uuid4().hex[:12]}@example.com"
        register_response = await ac.post(
            "/api/v1/users", json={"email": email, "full_name": "E2E Test"}
        )
        assert register_response.status_code == 201
        body = register_response.json()
        assert body["email"] == email
        api_key = body["api_key"]

        me_response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {api_key}"})
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email

        no_key_response = await ac.get("/api/v1/users/me")
        assert no_key_response.status_code == 401

        wrong_key_response = await ac.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer rsag_wrongwrongwrongwrongwrongwrongwrong"},
        )
        assert wrong_key_response.status_code == 401


async def test_duplicate_registration_returns_409(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        email = f"e2e-dup-{uuid.uuid4().hex[:12]}@example.com"
        first = await ac.post("/api/v1/users", json={"email": email})
        assert first.status_code == 201

        second = await ac.post("/api/v1/users", json={"email": email})
        assert second.status_code == 409
