"""Regression test for the resume ingestion file/text validation bug:
`if not request.file or not request.text` incorrectly required BOTH file
and text to be present, 400ing the two valid use cases (file-only,
text-only) it was meant to accept.

Note: ResumeIngestionRequest is parsed as a JSON body (no Form()/File()
markers on the endpoint), so a real UploadFile can never actually reach it
over HTTP - that's a pre-existing, separate limitation of the endpoint's
signature, not something this fix touches. The file-only branch of the
validation is therefore exercised by calling the endpoint function
directly with a stand-in truthy `file` value, bypassing HTTP/multipart
entirely, rather than via a (currently unsupported) real file upload.
"""
import pytest

from app.api.dependencies import get_resume_service
from app.api.v1.endpoints.resume import post_ingest_resume
from app.schemas.resume import ResumeIngestionRequest


class _FakeResumeService:
    """Stands in for ResumeSerives so this test never touches Postgres
    or loads the embedding model."""

    async def resume_ingest(self, request, user_id):
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
        json={"title": "My Resume", "text": "Some resume text long enough to pass validation"},
        headers=headers,
    )
    assert response.status_code == 200


def test_neither_file_nor_text_is_rejected(client_with_fake_resume_service, authed_user):
    _, _, headers = authed_user
    response = client_with_fake_resume_service.post(
        "/api/v1/resume/ingest",
        json={"title": "My Resume"},
        headers=headers,
    )
    assert response.status_code == 400


async def test_file_only_is_accepted(authed_user):
    user, _, _ = authed_user
    # model_construct bypasses Pydantic's UploadFile type validation - this
    # test only needs `file` to be truthy, not a real upload, since it's
    # exercising the endpoint's own `if not file and not text` boolean logic.
    request = ResumeIngestionRequest.model_construct(
        title="My Resume", file="stand-in-truthy-file-value", text=None
    )

    result = await post_ingest_resume(request, current_user=user, service=_FakeResumeService())

    assert result.status == "success"
