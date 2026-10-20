"""Schemas for the user's career-agent command center."""
from typing import Literal
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.application import ApplicationSummaryResponse
from app.schemas.profile import CareerPreferenceResponse, TargetRoleResponse


class CareerAction(BaseModel):
    title: str
    description: str
    href: str
    priority: Literal["urgent", "ready", "build"]


class CareerProfileReadiness(BaseModel):
    score: int = Field(ge=0, le=100)
    identity: bool
    summary: bool
    skills: bool
    work_history: bool
    verified_evidence: bool


class CareerSummaryResponse(BaseModel):
    display_name: str | None = None
    profile_readiness: CareerProfileReadiness
    skill_gaps: list[str]
    strong_matches: list[str]
    tailoring_recommendations: list[str]
    durable_match_count: int
    active_applications: int
    average_match_score: int | None = None
    recent_applications: list[ApplicationSummaryResponse]
    next_actions: list[CareerAction]
    preferences: CareerPreferenceResponse
    target_roles: list[TargetRoleResponse]

class FeedbackCreate(BaseModel):
    subject_type: Literal["match", "artifact", "recommendation"]
    subject_id: UUID
    feedback_type: Literal["useful", "not_useful", "correction", "quality"]
    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = Field(None, max_length=5000)
