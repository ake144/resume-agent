"""Tests for structured, user-verifiable career evidence."""
import uuid


def test_evidence_crud_and_resume_provenance_validation(client, authed_user):
    _, _, headers = authed_user

    created = client.post(
        "/api/v1/profile/evidence",
        headers=headers,
        json={
            "evidence_type": "accomplishment",
            "title": "Improved checkout performance",
            "description": "Reduced checkout load time after profiling the React application.",
            "source": "user_entered",
            "verified": True,
        },
    )

    assert created.status_code == 201
    evidence = created.json()
    assert evidence["verified"] is True
    assert evidence["source"] == "user_entered"

    listed = client.get("/api/v1/profile/evidence", headers=headers)
    updated = client.put(
        f"/api/v1/profile/evidence/{evidence['id']}",
        headers=headers,
        json={"title": "Improved checkout performance (verified)"},
    )
    deleted = client.delete(f"/api/v1/profile/evidence/{evidence['id']}", headers=headers)

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert updated.status_code == 200
    assert updated.json()["title"].endswith("(verified)")
    assert deleted.status_code == 204

    foreign_resume_reference = client.post(
        "/api/v1/profile/evidence",
        headers=headers,
        json={
            "evidence_type": "project",
            "title": "Invalid provenance",
            "description": "This must not reference another user's resume.",
            "source_resume_version_id": str(uuid.uuid4()),
        },
    )
    assert foreign_resume_reference.status_code == 404
