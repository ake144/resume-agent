"""Tests for target roles and career-search preferences."""


def test_preferences_and_target_roles_are_user_scoped(client, authed_user):
    _, _, headers = authed_user

    saved = client.put(
        "/api/v1/profile/preferences",
        headers=headers,
        json={
            "work_modes": ["remote"],
            "employment_types": ["full_time"],
            "preferred_locations": ["International"],
            "minimum_salary": 90000,
            "salary_currency": "USD",
            "willing_to_relocate": False,
            "visa_sponsorship_required": True,
        },
    )
    role = client.post(
        "/api/v1/profile/target-roles",
        headers=headers,
        json={"role_name": "Senior Frontend Engineer", "priority": 1},
    )
    duplicate = client.post(
        "/api/v1/profile/target-roles",
        headers=headers,
        json={"role_name": "Senior Frontend Engineer", "priority": 2},
    )
    listed = client.get("/api/v1/profile/target-roles", headers=headers)

    assert saved.status_code == 200
    assert saved.json()["work_modes"] == ["remote"]
    assert saved.json()["visa_sponsorship_required"] is True
    assert role.status_code == 201
    assert duplicate.status_code == 409
    assert listed.status_code == 200
    assert listed.json()[0]["role_name"] == "Senior Frontend Engineer"

    role_id = role.json()["id"]
    deleted = client.delete(f"/api/v1/profile/target-roles/{role_id}", headers=headers)
    assert deleted.status_code == 204
