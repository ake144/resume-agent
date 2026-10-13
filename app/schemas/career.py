"""Schemas for the user's career-agent command center."""
from typing import Literal
from pydantic import BaseModel, Field

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
    active_applications: int
    average_match_score: int | None = None
    recent_applications: list[ApplicationSummaryResponse]
    next_actions: list[CareerAction]
    preferences: CareerPreferenceResponse
    target_roles: list[TargetRoleResponse]
