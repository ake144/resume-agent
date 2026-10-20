"""API-key rotation preserves session users while invalidating the old key."""


def test_rotating_api_key_invalidates_the_previous_key(client, authed_user):
    _, old_key, headers = authed_user

    response = client.post("/api/v1/users/api-key/rotate", headers=headers)

    assert response.status_code == 200
    new_key = response.json()["api_key"]
    assert new_key != old_key
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {old_key}"}).status_code == 401
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {new_key}"}).status_code == 200
