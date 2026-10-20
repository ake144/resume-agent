import uuid
import pytest

from app.db.models import Application
from app.schemas.application import ApplicationType
from app.schemas.interview import InterviewAnswerCreate, InterviewSessionCreate
from app.services.interview_service import InterviewService


def test_interview_session_and_answer_are_user_scoped(db_session, authed_user):
    user, _, _ = authed_user
    application = Application(user_id=user.id, application_type=ApplicationType.INTERVIEW_PREP, job_title="Engineer", generated_content="Draft")
    db_session.add(application); db_session.commit()
    service = InterviewService()
    session = service.create_session(db_session, str(user.id), InterviewSessionCreate(application_id=application.id, question_set=["Tell me about a project."]))
    answer = service.add_answer(db_session, str(user.id), session.id, InterviewAnswerCreate(question_index=0, answer="A grounded answer."))
    assert session.application_id == application.id
    assert answer.question_index == 0
    with pytest.raises(Exception):
        service.add_answer(db_session, str(uuid.uuid4()), session.id, InterviewAnswerCreate(question_index=0, answer="No access"))
    service.delete_session(db_session, str(user.id), session.id)
    assert service.list_sessions(db_session, str(user.id)) == []
