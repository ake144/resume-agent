"""add career evidence

Revision ID: 3b6c8d9e0f11
Revises: 2a5b7c8d9e10
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3b6c8d9e0f11"
down_revision: Union[str, Sequence[str], None] = "2a5b7c8d9e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("source_resume_version_id", sa.UUID(), nullable=True),
        sa.Column("evidence_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_resume_version_id"], ["resume_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_evidence_user_id", "career_evidence", ["user_id"])
    op.create_index("ix_career_evidence_user_id_type", "career_evidence", ["user_id", "evidence_type"])


def downgrade() -> None:
    op.drop_index("ix_career_evidence_user_id_type", table_name="career_evidence")
    op.drop_index("ix_career_evidence_user_id", table_name="career_evidence")
    op.drop_table("career_evidence")
