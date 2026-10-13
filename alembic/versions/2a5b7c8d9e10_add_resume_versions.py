"""add immutable resume versions

Revision ID: 2a5b7c8d9e10
Revises: 7df60d029214
Create Date: 2026-10-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2a5b7c8d9e10"
down_revision: Union[str, Sequence[str], None] = "7df60d029214"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resume_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("data", sa.LargeBinary(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("parser_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "content_hash", name="uq_resume_versions_user_id_content_hash"),
    )
    op.create_index("ix_resume_versions_user_id", "resume_versions", ["user_id"])
    op.create_index(
        "ix_resume_versions_user_id_created_at",
        "resume_versions",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_resume_versions_user_id_created_at", table_name="resume_versions")
    op.drop_index("ix_resume_versions_user_id", table_name="resume_versions")
    op.drop_table("resume_versions")
