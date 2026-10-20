"""Schemas for grounded interview-practice sessions."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class InterviewSessionCreate(BaseModel):
    application_id: UUID
    stage: str = Field("screening", min_length=1, max_length=50)
    scheduled_at: Optional[datetime] = None
    question_set: list[str] = Field(default_factory=list)


class InterviewSessionResponse(InterviewSessionCreate):
    id: UUID
    improvement_plan: list[str]
    created_at: datetime
    class Config: from_attributes = True


class InterviewAnswerCreate(BaseModel):
    question_index: int = Field(..., ge=0)
    answer: str = Field(..., min_length=1, max_length=20000)


class InterviewAnswerResponse(InterviewAnswerCreate):
    id: UUID
    feedback: Optional[str] = None
    rubric_score: Optional[int] = None
    created_at: datetime
    class Config: from_attributes = True
