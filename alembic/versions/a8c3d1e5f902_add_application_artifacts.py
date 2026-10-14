"""add immutable application artifacts

Revision ID: a8c3d1e5f902
Revises: 9a4e7b2c6d11
Create Date: 2026-10-14 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a8c3d1e5f902"
down_revision: Union[str, Sequence[str], None] = "9a4e7b2c6d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_artifacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("parent_artifact_id", sa.UUID(), nullable=True),
        sa.Column("artifact_type", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence_citations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("unsupported_claims", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_artifact_id"], ["application_artifacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_application_artifacts_user_id", "application_artifacts", ["user_id"])
    op.create_index("ix_application_artifacts_application_id", "application_artifacts", ["application_id"])
    op.create_index("ix_application_artifacts_parent_artifact_id", "application_artifacts", ["parent_artifact_id"])
    op.create_index("ix_application_artifacts_application_created", "application_artifacts", ["application_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_application_artifacts_application_created", table_name="application_artifacts")
    op.drop_index("ix_application_artifacts_parent_artifact_id", table_name="application_artifacts")
    op.drop_index("ix_application_artifacts_application_id", table_name="application_artifacts")
    op.drop_index("ix_application_artifacts_user_id", table_name="application_artifacts")
    op.drop_table("application_artifacts")
