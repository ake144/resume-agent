"""Regression tests for resume ingestion:

1. The file/text validation bug: `if not request.file or not request.text`
   incorrectly required BOTH file and text to be present, 400ing the two
   valid use cases (file-only, text-only) it was meant to accept.
2. The multipart bug: the endpoint used to be a bare Pydantic-model JSON
   body (no Form()/File() markers), so a real UploadFile could never
   actually reach it over HTTP - only `text` worked. Now that the endpoint
   uses explicit Form()/File() params, a genuine multipart file upload is
   exercised here for real, not worked around.
"""
import pytest

from app.api.dependencies import get_resume_service


class _FakeResumeService:
    """Stands in for ResumeSerives so this test never touches Postgres
    or loads the embedding model."""

    async def resume_ingest(self, user_id, file, text, title):
        return {"status": "success", "chunks_ingested": 1, "user_id": user_id}


@pytest.fixture()
def client_with_fake_resume_service(client):
    client.app.dependency_overrides[get_resume_service] = lambda: _FakeResumeService()
    yield client
    client.app.dependency_overrides.pop(get_resume_service, None)


def test_text_only_is_accepted(client_with_fake_resume_service, authed_user):
    _, _, headers = authed_user
    response = client_with_fake_resume_service.post(
        "/api/v1/resume/ingest",
        data={"title": "My Resume", "text": "Some resume text long enough to pass validation"},
        headers=headers,
    )
    assert response.status_code == 200


def test_file_only_is_accepted(client_with_fake_resume_service, authed_user):
    _, _, headers = authed_user
    response = client_with_fake_resume_service.post(
        "/api/v1/resume/ingest",
        data={"title": "My Resume"},
        files={"file": ("resume.txt", b"Some resume text", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 200


def test_neither_file_nor_text_is_rejected(client_with_fake_resume_service, authed_user):
    _, _, headers = authed_user
    response = client_with_fake_resume_service.post(
        "/api/v1/resume/ingest",
        data={"title": "My Resume"},
        headers=headers,
    )
    assert response.status_code == 400
