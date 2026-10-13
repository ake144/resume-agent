"""Career-agent summary endpoints."""
from datetime import datetime, timezone
from typing import Annotated
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.db.models import Application, CareerEvidence, CareerPreference, SkillEntry, TargetRole, User, UserProfile, WorkHistoryEntry
from app.schemas.application import ApplicationStatus
from app.schemas.career import (
    CareerAction,
    CareerProfileReadiness,
    CareerSummaryResponse,
)

router = APIRouter(tags=["career"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/summary",
    response_model=CareerSummaryResponse,
    summary="Get the authenticated user's career-agent summary",
)
def get_career_summary(current_user: CurrentUser, db: DbSession) -> CareerSummaryResponse:
    """Build the command-center snapshot from user-owned relational data.

    This endpoint intentionally uses stored evidence only. It does not infer
    skills from titles or manufacture recommendations from missing data.
    """
    profile = db.get(UserProfile, current_user.id)
    skills = db.query(SkillEntry).filter(SkillEntry.user_id == current_user.id).all()
    work_history = (
        db.query(WorkHistoryEntry)
        .filter(WorkHistoryEntry.user_id == current_user.id)
        .all()
    )
    verified_evidence = (
        db.query(CareerEvidence)
        .filter(CareerEvidence.user_id == current_user.id, CareerEvidence.verified.is_(True))
        .count()
        > 0
    )
    applications = (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
        .limit(6)
        .all()
    )
    preferences = db.get(CareerPreference, current_user.id)
    if preferences is None:
        preferences = CareerPreference(user_id=current_user.id)
        preferences.updated_at = datetime.now(timezone.utc)
    target_roles = (
        db.query(TargetRole)
        .filter(TargetRole.user_id == current_user.id)
        .order_by(TargetRole.priority.asc(), TargetRole.created_at.asc())
        .all()
    )

    identity_complete = bool(
        profile and profile.full_name and (profile.contact_email or current_user.email)
    )
    summary_complete = bool(profile and profile.summary)
    skills_complete = bool(skills)
    work_history_complete = bool(work_history)
    evidence_complete = verified_evidence
    readiness_signals = [
        identity_complete,
        summary_complete,
        skills_complete,
        work_history_complete,
        evidence_complete,
    ]
    readiness = CareerProfileReadiness(
        score=round(sum(readiness_signals) / len(readiness_signals) * 100),
        identity=identity_complete,
        summary=summary_complete,
        skills=skills_complete,
        work_history=work_history_complete,
        verified_evidence=evidence_complete,
    )

    gap_counter: Counter[str] = Counter()
    for application in applications:
        analysis = application.match_analysis or {}
        for gap in analysis.get("skill_gaps", []):
            if isinstance(gap, str) and gap.strip():
                gap_counter[gap.strip()] += 1

    match_scores = [
        application.match_score
        for application in applications
        if application.match_score is not None
    ]
    active_statuses = {
        ApplicationStatus.DRAFT,
        ApplicationStatus.GENERATED,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.INTERVIEWING,
    }
    active_applications = sum(application.status in active_statuses for application in applications)

    actions: list[CareerAction] = []
    if readiness.score < 100:
        actions.append(
            CareerAction(
                title="Complete your career profile",
                description="Add the missing evidence the agent needs to make grounded recommendations.",
                href="/dashboard/settings",
                priority="urgent",
            )
        )
    if gap_counter:
        actions.append(
            CareerAction(
                title="Close a recurring skill gap",
                description=f"Review {gap_counter.most_common(1)[0][0]} before your next application.",
                href="/dashboard/roadmap",
                priority="build",
            )
        )
    if applications:
        actions.append(
            CareerAction(
                title="Review your latest application",
                description="Validate its evidence and next step before sending it on.",
                href=f"/dashboard/slays/{applications[0].id}",
                priority="ready",
            )
        )
    else:
        actions.append(
            CareerAction(
                title="Analyze your first target role",
                description="Paste a job description to generate a grounded application package.",
                href="/dashboard/workspace",
                priority="ready",
            )
        )

    return CareerSummaryResponse(
        display_name=profile.full_name if profile else None,
        profile_readiness=readiness,
        skill_gaps=[gap for gap, _ in gap_counter.most_common(8)],
        active_applications=active_applications,
        average_match_score=round(sum(match_scores) / len(match_scores)) if match_scores else None,
        recent_applications=applications,
        next_actions=actions,
        preferences=preferences,
        target_roles=target_roles,
    )
