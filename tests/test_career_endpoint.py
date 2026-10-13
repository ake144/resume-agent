"""Tests for the authenticated career-agent summary."""
from datetime import date

from app.db.models import Application, SkillEntry, WorkHistoryEntry
from app.schemas.application import ApplicationStatus, ApplicationType


def test_career_summary_reports_owned_readiness_and_gaps(client, db_session, authed_user):
    user, raw_key, _ = authed_user
    profile = user.id
    db_session.add(SkillEntry(user_id=profile, name="React", proficiency="advanced"))
    db_session.add(
        WorkHistoryEntry(
            user_id=profile,
            company="Example Co",
            job_title="Frontend Engineer",
            start_date=date(2022, 1, 1),
            description="Built production interfaces.",
        )
    )
    db_session.add(
        Application(
            user_id=profile,
            application_type=ApplicationType.RESUME_TAILORING,
            status=ApplicationStatus.GENERATED,
            job_title="Senior Frontend Engineer",
            generated_content="Tailored resume",
            match_score=84,
            match_analysis={"skill_gaps": ["Playwright", "Playwright"]},
        )
    )
    db_session.commit()

    response = client.get("/api/v1/career/summary", headers={"Authorization": f"Bearer {raw_key}"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile_readiness"]["score"] == 40
    assert payload["profile_readiness"]["verified_evidence"] is False
    assert payload["active_applications"] == 1
    assert payload["average_match_score"] == 84
    assert payload["skill_gaps"] == ["Playwright"]
    assert payload["recent_applications"][0]["job_title"] == "Senior Frontend Engineer"


def test_career_summary_requires_authentication(client):
    response = client.get("/api/v1/career/summary")

    assert response.status_code in {401, 403}
