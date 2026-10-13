"""Tests for local and international source presets."""


def test_local_source_catalog_includes_ethiopian_and_international_workflows(client):
    response = client.get("/api/v1/jobs/local-sources")

    assert response.status_code == 200
    providers = {item["provider"] for item in response.json()}
    assert {"ethiojobs_manual", "hahu_manual", "harmee_manual", "linkedin_manual", "telegram_manual"} <= providers
    assert all(item["mode"] in {"link_or_paste", "forward_or_paste"} for item in response.json())
