"""Tests for user-owned job source configuration."""


def test_source_configuration_and_ingestion_metadata(client, db_session, authed_user):
    _, _, headers = authed_user

    created = client.post(
        "/api/v1/jobs/sources",
        headers=headers,
        json={"provider": "greenhouse", "source_key": "example-co", "config": {"board": "example"}},
    )
    assert created.status_code == 201
    source = created.json()["data"]

    listed = client.get("/api/v1/jobs/sources", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["data"][0]["provider"] == "greenhouse"

    duplicate = client.post(
        "/api/v1/jobs/sources",
        headers=headers,
        json={"provider": "greenhouse", "source_key": "example-co"},
    )
    assert duplicate.status_code == 409

