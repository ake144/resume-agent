"""Tests for durable, user-scoped job match results."""
from unittest.mock import AsyncMock, patch

from app.db.models import JobPosting, MatchResult
from app.schemas.job import JobMatchRequest, RankJobPostingsRequest
from app.services.job_service import JobService


async def test_matching_persists_a_versioned_result(db_session, authed_user):
    user, _, _ = authed_user
    posting = JobPosting(
        user_id=user.id,
        title="Senior Frontend Engineer",
        description="React and TypeScript role",
        source_type="manual_paste",
    )
    db_session.add(posting)
    db_session.flush()

    fake_result = {
        "analysis": type(
            "Analysis",
            (),
            {
                "match_score": 88,
                "confidence_level": "High",
                "preference_alignment": "No explicit conflict found",
                "strong_matches": ["React experience"],
                "skill_gaps": ["Playwright"],
                "tailoring_recommendations": ["Highlight testing work"],
                "hard_constraints": [],
            },
        )(),
        "sources": [{"type": "resume", "title": "Primary resume"}],
        "sources_used": 1,
    }
    request = JobMatchRequest(
        job_text=posting.description,
        job_title=posting.title,
        job_posting_id=posting.id,
    )

    with patch("app.services.job_service.match_job_to_user", new=AsyncMock(return_value=fake_result)):
        await JobService().match_job(request, str(user.id), db_session)

    saved = db_session.query(MatchResult).one()
    assert saved.job_posting_id == posting.id
    assert saved.match_score == 88
    assert saved.skill_gaps == ["Playwright"]
    assert saved.matcher_version == "preferences-v1"


def test_match_result_routes_are_user_scoped(client, db_session, authed_user):
    user, _, headers = authed_user
    posting = JobPosting(user_id=user.id, title="Engineer", description="Role", source_type="manual_paste")
    db_session.add(posting)
    db_session.flush()
    result = MatchResult(
        user_id=user.id,
        job_posting_id=posting.id,
        matcher_version="preferences-v1",
        match_score=75,
        confidence_level="Medium",
        preference_alignment="Unknown",
        strong_matches=["Python"],
        skill_gaps=[],
        tailoring_recommendations=[],
        hard_constraints=[],
        sources=[],
    )
    db_session.add(result)
    db_session.commit()

    listed = client.get("/api/v1/jobs/matches", headers=headers)
    detail = client.get(f"/api/v1/jobs/matches/{result.id}", headers=headers)

    assert listed.status_code == 200
    assert listed.json()["data"][0]["match_score"] == 75
    assert detail.status_code == 200
    assert detail.json()["data"]["job_posting_id"] == str(posting.id)


async def test_ranking_only_evaluates_active_unranked_postings(db_session, authed_user):
    user, _, _ = authed_user
    active = JobPosting(user_id=user.id, title="Active role", description="React", source_type="greenhouse")
    already_ranked = JobPosting(user_id=user.id, title="Ranked role", description="TypeScript", source_type="greenhouse")
    db_session.add_all([active, already_ranked])
    db_session.flush()
    db_session.add(
        MatchResult(
            user_id=user.id,
            job_posting_id=already_ranked.id,
            matcher_version="preferences-v1",
            match_score=70,
            confidence_level="Medium",
            preference_alignment="Unknown",
            strong_matches=[], skill_gaps=[], tailoring_recommendations=[], hard_constraints=[], sources=[],
        )
    )
    db_session.commit()
    fake_result = {
        "analysis": type("Analysis", (), {
            "match_score": 92, "confidence_level": "High", "preference_alignment": "No explicit conflict found",
            "strong_matches": ["React"], "skill_gaps": [], "tailoring_recommendations": [], "hard_constraints": [],
        })(),
        "sources": [],
    }

    with patch("app.services.job_service.match_job_to_user", new=AsyncMock(return_value=fake_result)) as matcher:
        result = await JobService().rank_job_postings(
            db_session, str(user.id), RankJobPostingsRequest(limit=10)
        )

    assert result.evaluated == 1
    assert result.skipped == 1
    assert matcher.await_count == 1
    assert db_session.query(MatchResult).filter(MatchResult.job_posting_id == active.id).one().match_score == 92
