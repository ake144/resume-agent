"""Endpoints for the authenticated user's structured profile data:
contact info, work history, education, and skills.
"""
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_profile_service
from app.core.database import get_db
from app.db.models import User
from app.schemas.profile import (
    EducationEntryCreate,
    EducationEntryResponse,
    EducationEntryUpdate,
    SkillEntryCreate,
    SkillEntryResponse,
    SkillEntryUpdate,
    UserProfileResponse,
    UserProfileUpdate,
    WorkHistoryEntryCreate,
    WorkHistoryEntryResponse,
    WorkHistoryEntryUpdate,
)
from app.services.profile_service import ProfileService

router = APIRouter(tags=["profile"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
ProfileSvc = Annotated[ProfileService, Depends(get_profile_service)]


# --- Profile ---

@router.get("", response_model=UserProfileResponse, summary="Get the authenticated user's profile")
def get_profile(current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    return service.get_profile(db, current_user.id)


@router.put("", response_model=UserProfileResponse, summary="Update the authenticated user's profile")
def update_profile(update: UserProfileUpdate, current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    return service.update_profile(db, current_user.id, update)


# --- Work history ---

@router.get(
    "/work-history", response_model=List[WorkHistoryEntryResponse], summary="List work history entries"
)
def list_work_history(current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    return service.list_work_history(db, current_user.id)


@router.post(
    "/work-history",
    response_model=WorkHistoryEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a work history entry",
)
def create_work_history(
    data: WorkHistoryEntryCreate, current_user: CurrentUser, db: DbSession, service: ProfileSvc
):
    return service.create_work_history(db, current_user.id, data)


@router.put(
    "/work-history/{entry_id}", response_model=WorkHistoryEntryResponse, summary="Update a work history entry"
)
def update_work_history(
    entry_id: UUID,
    update: WorkHistoryEntryUpdate,
    current_user: CurrentUser,
    db: DbSession,
    service: ProfileSvc,
):
    return service.update_work_history(db, current_user.id, entry_id, update)


@router.delete(
    "/work-history/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a work history entry"
)
def delete_work_history(entry_id: UUID, current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    service.delete_work_history(db, current_user.id, entry_id)


# --- Education ---

@router.get("/education", response_model=List[EducationEntryResponse], summary="List education entries")
def list_education(current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    return service.list_education(db, current_user.id)


@router.post(
    "/education",
    response_model=EducationEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an education entry",
)
def create_education(data: EducationEntryCreate, current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    return service.create_education(db, current_user.id, data)


@router.put("/education/{entry_id}", response_model=EducationEntryResponse, summary="Update an education entry")
def update_education(
    entry_id: UUID,
    update: EducationEntryUpdate,
    current_user: CurrentUser,
    db: DbSession,
    service: ProfileSvc,
):
    return service.update_education(db, current_user.id, entry_id, update)


@router.delete(
    "/education/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an education entry"
)
def delete_education(entry_id: UUID, current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    service.delete_education(db, current_user.id, entry_id)


# --- Skills ---

@router.get("/skills", response_model=List[SkillEntryResponse], summary="List skills")
def list_skills(current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    return service.list_skills(db, current_user.id)


@router.post(
    "/skills", response_model=SkillEntryResponse, status_code=status.HTTP_201_CREATED, summary="Add a skill"
)
def create_skill(data: SkillEntryCreate, current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    return service.create_skill(db, current_user.id, data)


@router.put("/skills/{entry_id}", response_model=SkillEntryResponse, summary="Update a skill")
def update_skill(
    entry_id: UUID, update: SkillEntryUpdate, current_user: CurrentUser, db: DbSession, service: ProfileSvc
):
    return service.update_skill(db, current_user.id, entry_id, update)


@router.delete("/skills/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a skill")
def delete_skill(entry_id: UUID, current_user: CurrentUser, db: DbSession, service: ProfileSvc):
    service.delete_skill(db, current_user.id, entry_id)
