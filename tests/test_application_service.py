"""Regression test for the /applications/generate breakage: the service
used to pass the full result dict from generate_application_package()
into ApplicationGenerationResponse.content, which is typed `str` -
Pydantic v2 doesn't coerce a dict into a str, so every call raised a
ValidationError (500) before this fix.
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.application import ApplicationGenerationRequest, ApplicationType
from app.services.application_service import ApplicationService


async def test_generate_application_constructs_response(db_session, authed_user):
    user, _, _ = authed_user

    fake_result = {
        "application_package": "cover_letter",
        "content": "Dear Hiring Manager...",
        "match_score": 85,
        "sources_used": 3,
        "match_analysis": {"match_score": 85, "overall_verdict": "Strong fit"},
    }
    request = ApplicationGenerationRequest(
        job_description="Some job description",
        job_title="Engineer",
        application_type=ApplicationType.COVER_LETTER,
    )

    with patch(
        "app.services.application_service.generate_application_package",
        new=AsyncMock(return_value=fake_result),
    ):
        service = ApplicationService()
        response = await service.generate_application(request, user_id=str(user.id), db=db_session)

    assert response.content == "Dear Hiring Manager..."
    assert response.match_score == 85
    assert response.sources_used == 3
    assert response.application_type == ApplicationType.COVER_LETTER


async def test_generate_application_requires_existing_user(db_session):
    """Application.user_id is a real FK - persisting for a nonexistent
    user must fail loudly, not silently succeed."""
    fake_result = {
        "application_package": "cover_letter",
        "content": "content",
        "match_score": 50,
        "sources_used": 0,
        "match_analysis": None,
    }
    request = ApplicationGenerationRequest(job_description="desc", job_title="Engineer")

    with patch(
        "app.services.application_service.generate_application_package",
        new=AsyncMock(return_value=fake_result),
    ):
        service = ApplicationService()
        with pytest.raises(Exception):
            await service.generate_application(request, user_id=str(uuid.uuid4()), db=db_session)
