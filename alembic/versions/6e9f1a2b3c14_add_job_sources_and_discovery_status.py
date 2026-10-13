"""add job sources and discovery status

Revision ID: 6e9f1a2b3c14
Revises: 5d8e0f1a2b13
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "6e9f1a2b3c14"
down_revision: Union[str, Sequence[str], None] = "5d8e0f1a2b13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "provider", "source_key", name="uq_job_sources_user_provider_key"),
    )
    op.create_index("ix_job_sources_user_id", "job_sources", ["user_id"])
    op.add_column("job_postings", sa.Column("source_id", sa.UUID(), nullable=True))
    op.add_column("job_postings", sa.Column("discovery_status", sa.String(length=30), nullable=True))
    op.execute("UPDATE job_postings SET discovery_status = 'discovered' WHERE discovery_status IS NULL")
    op.alter_column("job_postings", "discovery_status", nullable=False)
    op.create_foreign_key(
        "fk_job_postings_source_id_job_sources",
        "job_postings",
        "job_sources",
        ["source_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_job_postings_source_id", "job_postings", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_job_postings_source_id", table_name="job_postings")
    op.drop_constraint("fk_job_postings_source_id_job_sources", "job_postings", type_="foreignkey")
    op.drop_column("job_postings", "discovery_status")
    op.drop_column("job_postings", "source_id")
    op.drop_index("ix_job_sources_user_id", table_name="job_sources")
    op.drop_table("job_sources")
