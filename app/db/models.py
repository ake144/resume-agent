"""SQLAlchemy ORM models for the app's own relational tables.

These are distinct from PGVector's own tables (langchain_pg_collection /
langchain_pg_embedding), which are created and managed by langchain_postgres
itself against a completely separate declarative base. Alembic must only
ever be allowed to manage tables registered on `Base` here - see the
`include_name` filter in alembic/env.py.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.schemas.application import ApplicationStatus, ApplicationType


class User(Base, TimestampMixin):
    """Account/auth identity only - no display or career data here.

    Display/career data lives solely on UserProfile so identity and
    profile data aren't duplicated in two places.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_api_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserProfile(Base, TimestampMixin):
    """1:1 structured contact info. Auto-created (empty) at registration
    so downstream code never has to special-case "profile doesn't exist yet"."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    links: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class CareerPreference(Base, TimestampMixin):
    """One editable set of constraints used to rank future opportunities."""

    __tablename__ = "career_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    work_modes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    employment_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    preferred_locations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    minimum_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    willing_to_relocate: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    visa_sponsorship_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class TargetRole(Base, TimestampMixin):
    """A ranked role the user wants the agent to discover and evaluate."""

    __tablename__ = "target_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_name", name="uq_target_roles_user_id_role_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class WorkHistoryEntry(Base, TimestampMixin):
    """Normalized rather than a JSONB array: needs row-level edit/delete
    and typed dates for future ATS-autofill use, not just storage size."""

    __tablename__ = "work_history_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    # NULL end_date means current/ongoing - avoids a separate boolean that could contradict it
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class EducationEntry(Base, TimestampMixin):
    __tablename__ = "education_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # String, not Numeric: real-world GPA formats vary too much ("3.8", "3.8/4.0", "First Class Honours")
    gpa: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class SkillEntry(Base, TimestampMixin):
    __tablename__ = "skill_entries"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_skill_entries_user_id_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    proficiency: Mapped[str | None] = mapped_column(String(20), nullable=True)


class CareerEvidence(Base, TimestampMixin):
    """A user-owned professional claim with explicit provenance."""

    __tablename__ = "career_evidence"
    __table_args__ = (Index("ix_career_evidence_user_id_type", "user_id", "evidence_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True
    )
    evidence_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="user_entered")
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ResumeFile(Base):
    """Most-recent uploaded PDF resume only - overwritten on re-upload,
    not versioned. Only extracted text survives resume ingestion
    otherwise; this exists so auto-apply has an actual file to attach
    to ATS application forms.
    """

    __tablename__ = "resume_files"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ResumeVersion(Base, TimestampMixin):
    """Immutable resume snapshot used as career-profile evidence.

    The legacy ResumeFile row remains for compatibility with existing download
    consumers; new ingestion records are stored here instead of overwriting
    the user's previous resume.
    """

    __tablename__ = "resume_versions"
    __table_args__ = (
        Index("ix_resume_versions_user_id_created_at", "user_id", "created_at"),
        UniqueConstraint("user_id", "content_hash", name="uq_resume_versions_user_id_content_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_status: Mapped[str] = mapped_column(String(30), nullable=False, default="parsed")


class JobSource(Base, TimestampMixin):
    """A permitted source configuration for future discovery workers."""

    __tablename__ = "job_sources"
    __table_args__ = (UniqueConstraint("user_id", "provider", "source_key", name="uq_job_sources_user_provider_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    source_key: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class JobPosting(Base):
    """Structured job data. Complements, doesn't replace, the temp
    PGVector store: job ingestion still chunks+embeds the description for
    RAG matching, and additionally writes one row here with the structured
    fields (cross-linked via a job_posting_id metadata key on the chunks).

    No TimestampMixin: discovered_at plays the role of created_at, and
    rows are NOT swept by the vector-store TTL cleanup job (only the
    embeddings are) since an Application may reference a posting.
    """

    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("user_id", "source_url", name="uq_job_postings_user_id_source_url"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual_paste")
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    discovery_status: Mapped[str] = mapped_column(String(30), nullable=False, default="discovered")
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class MatchResult(Base, TimestampMixin):
    """Versioned snapshot of a user's evaluation of a job posting."""

    __tablename__ = "match_results"
    __table_args__ = (
        Index("ix_match_results_user_id_created_at", "user_id", "created_at"),
        Index("ix_match_results_job_posting_id_created_at", "job_posting_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # A match is a snapshot of the career material available at evaluation
    # time.  Keeping this nullable preserves older/manual matches made before
    # resume versioning was introduced.
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    matcher_version: Mapped[str] = mapped_column(String(50), nullable=False, default="preferences-v1")
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False)
    preference_alignment: Mapped[str] = mapped_column(String(40), nullable=False)
    strong_matches: Mapped[list] = mapped_column(JSONB, nullable=False)
    skill_gaps: Mapped[list] = mapped_column(JSONB, nullable=False)
    tailoring_recommendations: Mapped[list] = mapped_column(JSONB, nullable=False)
    hard_constraints: Mapped[list] = mapped_column(JSONB, nullable=False)
    sources: Mapped[list] = mapped_column(JSONB, nullable=False)


class Application(Base, TimestampMixin):
    """Tracking: what was applied to, when, with what generated content
    and result. Nothing persisted generated application content anywhere
    before this table existed."""

    __tablename__ = "applications"
    __table_args__ = (Index("ix_applications_user_id_status", "user_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Nullable + SET NULL so a future JobPosting purge can never silently destroy Application history
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    application_type: Mapped[ApplicationType] = mapped_column(
        SAEnum(
            ApplicationType,
            native_enum=False,
            validate_strings=True,
            length=50,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    # CHECK-constrained string, not a native Postgres ENUM: avoids an ALTER TYPE
    # migration every time the status vocabulary grows. values_callable makes the
    # persisted/checked strings match the enum's lowercase .value (e.g. "cover_letter"),
    # not its uppercase member .name - consistent with what the JSON API sends/returns.
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            native_enum=False,
            validate_strings=True,
            length=20,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ApplicationStatus.GENERATED,
    )
    # Denormalized snapshot at apply time, deliberately independent of job_postings
    # so a later edit/unlink can't rewrite application history
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_content: Mapped[str] = mapped_column(Text, nullable=False)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sources_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApplicationArtifact(Base, TimestampMixin):
    """An immutable generated document and its human-review decision.

    Artifact state is deliberately independent from Application.status: a
    document can be approved without claiming that an external application
    was submitted.  Revisions create a new row linked to its parent.
    """

    __tablename__ = "application_artifacts"
    __table_args__ = (Index("ix_application_artifacts_application_created", "application_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_artifacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="needs_review")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_citations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    unsupported_claims: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApplicationEvent(Base, TimestampMixin):
    """Immutable application-pipeline event; never infer submission from an artifact decision."""
    __tablename__ = "application_events"
    __table_args__ = (Index("ix_application_events_application_created", "application_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class ApplicationTask(Base, TimestampMixin):
    __tablename__ = "application_tasks"
    __table_args__ = (Index("ix_application_tasks_user_due", "user_id", "due_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApplicationContact(Base, TimestampMixin):
    __tablename__ = "application_contacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserFeedback(Base, TimestampMixin):
    __tablename__ = "user_feedback"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(40), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class InterviewSession(Base, TimestampMixin):
    __tablename__ = "interview_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="screening")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    question_set: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    improvement_plan: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class InterviewAnswer(Base, TimestampMixin):
    __tablename__ = "interview_answers"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    rubric_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
