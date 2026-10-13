"""CRUD operations for a user's structured profile data: contact info,
work history, education, and skills.
"""
import uuid
from typing import List, Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CareerEvidence, CareerPreference, EducationEntry, ResumeVersion, SkillEntry, TargetRole, UserProfile, WorkHistoryEntry
from app.schemas.profile import (
    EducationEntryCreate,
    EducationEntryUpdate,
    SkillEntryCreate,
    SkillEntryUpdate,
    UserProfileUpdate,
    WorkHistoryEntryCreate,
    WorkHistoryEntryUpdate,
    CareerEvidenceCreate,
    CareerEvidenceUpdate,
    CareerPreferenceUpdate,
    TargetRoleCreate,
    TargetRoleUpdate,
)

ModelT = TypeVar("ModelT", WorkHistoryEntry, EducationEntry, SkillEntry, CareerEvidence, TargetRole)


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


class ProfileService:
    """CRUD for UserProfile plus its child collections (work history,
    education, skills). Deliberately not wrapped in the generic
    log_info/log_error ceremony used by the LLM-calling services - these
    are plain, low-risk SQLAlchemy operations already covered by the
    global ErrorHandlingMiddleware.
    """

    # --- Profile (1:1, auto-created at registration) ---

    def get_profile(self, db: Session, user_id: uuid.UUID) -> UserProfile:
        profile = db.get(UserProfile, user_id)
        if profile is None:
            raise _not_found("Profile")
        return profile

    def update_profile(self, db: Session, user_id: uuid.UUID, update: UserProfileUpdate) -> UserProfile:
        profile = self.get_profile(db, user_id)
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        db.commit()
        db.refresh(profile)
        return profile

    # --- Shared ownership check for the child collections below ---

    def _get_owned(
        self, db: Session, model: Type[ModelT], entry_id: uuid.UUID, user_id: uuid.UUID, resource_name: str
    ) -> ModelT:
        entry = db.get(model, entry_id)
        if entry is None or entry.user_id != user_id:
            raise _not_found(resource_name)
        return entry

    # --- Work history ---

    def list_work_history(self, db: Session, user_id: uuid.UUID) -> List[WorkHistoryEntry]:
        return (
            db.query(WorkHistoryEntry)
            .filter(WorkHistoryEntry.user_id == user_id)
            .order_by(WorkHistoryEntry.start_date.desc())
            .all()
        )

    def create_work_history(
        self, db: Session, user_id: uuid.UUID, data: WorkHistoryEntryCreate
    ) -> WorkHistoryEntry:
        entry = WorkHistoryEntry(user_id=user_id, **data.model_dump())
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def update_work_history(
        self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID, update: WorkHistoryEntryUpdate
    ) -> WorkHistoryEntry:
        entry = self._get_owned(db, WorkHistoryEntry, entry_id, user_id, "Work history entry")
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        db.commit()
        db.refresh(entry)
        return entry

    def delete_work_history(self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        entry = self._get_owned(db, WorkHistoryEntry, entry_id, user_id, "Work history entry")
        db.delete(entry)
        db.commit()

    # --- Education ---

    def list_education(self, db: Session, user_id: uuid.UUID) -> List[EducationEntry]:
        return (
            db.query(EducationEntry)
            .filter(EducationEntry.user_id == user_id)
            .order_by(EducationEntry.start_date.desc().nullslast())
            .all()
        )

    def create_education(self, db: Session, user_id: uuid.UUID, data: EducationEntryCreate) -> EducationEntry:
        entry = EducationEntry(user_id=user_id, **data.model_dump())
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def update_education(
        self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID, update: EducationEntryUpdate
    ) -> EducationEntry:
        entry = self._get_owned(db, EducationEntry, entry_id, user_id, "Education entry")
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        db.commit()
        db.refresh(entry)
        return entry

    def delete_education(self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        entry = self._get_owned(db, EducationEntry, entry_id, user_id, "Education entry")
        db.delete(entry)
        db.commit()

    # --- Skills ---

    def list_skills(self, db: Session, user_id: uuid.UUID) -> List[SkillEntry]:
        return db.query(SkillEntry).filter(SkillEntry.user_id == user_id).order_by(SkillEntry.name).all()

    def create_skill(self, db: Session, user_id: uuid.UUID, data: SkillEntryCreate) -> SkillEntry:
        entry = SkillEntry(user_id=user_id, **data.model_dump())
        db.add(entry)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Skill '{data.name}' already exists",
            )
        db.refresh(entry)
        return entry

    def update_skill(
        self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID, update: SkillEntryUpdate
    ) -> SkillEntry:
        entry = self._get_owned(db, SkillEntry, entry_id, user_id, "Skill")
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Skill '{update.name}' already exists",
            )
        db.refresh(entry)
        return entry

    def delete_skill(self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        entry = self._get_owned(db, SkillEntry, entry_id, user_id, "Skill")
        db.delete(entry)
        db.commit()

    # --- Career evidence ---

    def list_evidence(self, db: Session, user_id: uuid.UUID) -> List[CareerEvidence]:
        return (
            db.query(CareerEvidence)
            .filter(CareerEvidence.user_id == user_id)
            .order_by(CareerEvidence.created_at.desc())
            .all()
        )

    def create_evidence(
        self, db: Session, user_id: uuid.UUID, data: CareerEvidenceCreate
    ) -> CareerEvidence:
        values = data.model_dump()
        source_resume_version_id = values.get("source_resume_version_id")
        if source_resume_version_id is not None:
            resume_version = db.get(ResumeVersion, source_resume_version_id)
            if resume_version is None or resume_version.user_id != user_id:
                raise _not_found("Resume version")
        evidence = CareerEvidence(user_id=user_id, **values)
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    def update_evidence(
        self,
        db: Session,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
        update: CareerEvidenceUpdate,
    ) -> CareerEvidence:
        evidence = self._get_owned(db, CareerEvidence, entry_id, user_id, "Career evidence")
        values = update.model_dump(exclude_unset=True)
        source_resume_version_id = values.get("source_resume_version_id")
        if source_resume_version_id is not None:
            resume_version = db.get(ResumeVersion, source_resume_version_id)
            if resume_version is None or resume_version.user_id != user_id:
                raise _not_found("Resume version")
        for field, value in values.items():
            setattr(evidence, field, value)
        db.commit()
        db.refresh(evidence)
        return evidence

    def delete_evidence(self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        evidence = self._get_owned(db, CareerEvidence, entry_id, user_id, "Career evidence")
        db.delete(evidence)
        db.commit()

    # --- Preferences and target roles ---

    def get_preferences(self, db: Session, user_id: uuid.UUID) -> CareerPreference:
        preferences = db.get(CareerPreference, user_id)
        if preferences is None:
            preferences = CareerPreference(user_id=user_id)
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        return preferences

    def update_preferences(
        self, db: Session, user_id: uuid.UUID, update: CareerPreferenceUpdate
    ) -> CareerPreference:
        preferences = self.get_preferences(db, user_id)
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(preferences, field, value)
        db.commit()
        db.refresh(preferences)
        return preferences

    def list_target_roles(self, db: Session, user_id: uuid.UUID) -> List[TargetRole]:
        return (
            db.query(TargetRole)
            .filter(TargetRole.user_id == user_id)
            .order_by(TargetRole.priority.asc(), TargetRole.created_at.asc())
            .all()
        )

    def create_target_role(
        self, db: Session, user_id: uuid.UUID, data: TargetRoleCreate
    ) -> TargetRole:
        role = TargetRole(user_id=user_id, **data.model_dump())
        db.add(role)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target role already exists")
        db.refresh(role)
        return role

    def update_target_role(
        self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID, update: TargetRoleUpdate
    ) -> TargetRole:
        role = self._get_owned(db, TargetRole, entry_id, user_id, "Target role")
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target role already exists")
        db.refresh(role)
        return role

    def delete_target_role(self, db: Session, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        role = self._get_owned(db, TargetRole, entry_id, user_id, "Target role")
        db.delete(role)
        db.commit()
