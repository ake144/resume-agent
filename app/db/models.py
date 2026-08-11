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
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


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
