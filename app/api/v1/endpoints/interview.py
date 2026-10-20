from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.db.models import User
from app.schemas.base import APIResponse
from app.schemas.interview import InterviewAnswerCreate, InterviewSessionCreate
from app.services.interview_service import InterviewService

router = APIRouter(tags=["interviews"])

@router.post("/sessions", response_model=APIResponse)
def create_session(request: InterviewSessionCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return APIResponse(status="success", message="Interview session created", data=InterviewService().create_session(db, str(user.id), request))

@router.get("/sessions", response_model=APIResponse)
def list_sessions(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], application_id: UUID | None = None):
    return APIResponse(status="success", message="Interview sessions retrieved", data=InterviewService().list_sessions(db, str(user.id), application_id))

@router.post("/sessions/{session_id}/answers", response_model=APIResponse)
def add_answer(session_id: UUID, request: InterviewAnswerCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return APIResponse(status="success", message="Interview answer saved", data=InterviewService().add_answer(db, str(user.id), session_id, request))

@router.get("/sessions/{session_id}/answers", response_model=APIResponse)
def list_answers(session_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return APIResponse(status="success", message="Interview answers retrieved", data=InterviewService().list_answers(db, str(user.id), session_id))

@router.delete("/sessions/{session_id}", response_model=APIResponse)
def delete_session(session_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    InterviewService().delete_session(db, str(user.id), session_id)
    return APIResponse(status="success", message="Interview session and answers deleted")
