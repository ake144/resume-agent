import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import Application, InterviewAnswer, InterviewSession
from app.schemas.interview import InterviewAnswerCreate, InterviewAnswerResponse, InterviewSessionCreate, InterviewSessionResponse


class InterviewService:
    @staticmethod
    def _rubric(answer: str) -> tuple[int, str]:
        """Explainable coaching only; it does not claim to assess factual truth."""
        words = len(answer.split())
        lower = answer.lower()
        structure = sum(marker in lower for marker in ("situation", "task", "action", "result"))
        score = min(100, min(words, 80) + structure * 5)
        advice = []
        if words < 60: advice.append("Add concrete context, actions, and an outcome.")
        if structure < 2: advice.append("Use a clear Situation–Task–Action–Result structure.")
        if not any(char.isdigit() for char in answer): advice.append("If verified, include a measurable outcome; otherwise describe the result plainly.")
        return score, " ".join(advice) or "Clear, structured response. Verify every stated detail before using it in an interview."
    def create_session(self, db: Session, user_id: str, data: InterviewSessionCreate) -> InterviewSessionResponse:
        user_uuid = uuid.UUID(user_id)
        application = db.get(Application, data.application_id)
        if application is None or application.user_id != user_uuid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        values = data.model_dump()
        if not values["question_set"]:
            analysis = application.match_analysis or {}
            questions = [f"Tell me about the experience that best prepares you for this {application.job_title} role."]
            questions.extend(
                f"What specific example supports your experience with {strength}?"
                for strength in analysis.get("strong_matches", [])[:3]
                if isinstance(strength, str)
            )
            questions.extend(
                f"How would you approach developing or addressing {gap} in this role?"
                for gap in analysis.get("skill_gaps", [])[:2]
                if isinstance(gap, str)
            )
            values["question_set"] = questions
        session = InterviewSession(user_id=user_uuid, **values)
        db.add(session); db.commit(); db.refresh(session)
        return InterviewSessionResponse.model_validate(session)

    def list_sessions(self, db: Session, user_id: str, application_id: uuid.UUID | None = None) -> list[InterviewSessionResponse]:
        query = db.query(InterviewSession).filter(InterviewSession.user_id == uuid.UUID(user_id))
        if application_id is not None: query = query.filter(InterviewSession.application_id == application_id)
        return [InterviewSessionResponse.model_validate(row) for row in query.order_by(InterviewSession.created_at.desc()).all()]

    def add_answer(self, db: Session, user_id: str, session_id: uuid.UUID, data: InterviewAnswerCreate) -> InterviewAnswerResponse:
        user_uuid = uuid.UUID(user_id)
        session = db.get(InterviewSession, session_id)
        if session is None or session.user_id != user_uuid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
        score, feedback = self._rubric(data.answer)
        answer = InterviewAnswer(user_id=user_uuid, interview_session_id=session.id, feedback=feedback, rubric_score=score, **data.model_dump())
        db.add(answer); db.commit(); db.refresh(answer)
        return InterviewAnswerResponse.model_validate(answer)

    def list_answers(self, db: Session, user_id: str, session_id: uuid.UUID) -> list[InterviewAnswerResponse]:
        session = db.get(InterviewSession, session_id)
        if session is None or session.user_id != uuid.UUID(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
        rows = db.query(InterviewAnswer).filter(InterviewAnswer.interview_session_id == session_id, InterviewAnswer.user_id == session.user_id).order_by(InterviewAnswer.question_index, InterviewAnswer.created_at).all()
        return [InterviewAnswerResponse.model_validate(row) for row in rows]

    def delete_session(self, db: Session, user_id: str, session_id: uuid.UUID) -> None:
        session = db.get(InterviewSession, session_id)
        if session is None or session.user_id != uuid.UUID(user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
        # The schema foreign key is ON DELETE CASCADE, so answer transcripts
        # and their coaching feedback are removed with this session.
        db.delete(session)
        db.commit()
