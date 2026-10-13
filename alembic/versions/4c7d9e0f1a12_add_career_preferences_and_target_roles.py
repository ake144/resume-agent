"""add career preferences and target roles

Revision ID: 4c7d9e0f1a12
Revises: 3b6c8d9e0f11
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "4c7d9e0f1a12"
down_revision: Union[str, Sequence[str], None] = "3b6c8d9e0f11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_preferences",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("work_modes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("employment_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("preferred_locations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("minimum_salary", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=True),
        sa.Column("willing_to_relocate", sa.Boolean(), nullable=True),
        sa.Column("visa_sponsorship_required", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "target_roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_name", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_name", name="uq_target_roles_user_id_role_name"),
    )
    op.create_index("ix_target_roles_user_id", "target_roles", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_target_roles_user_id", table_name="target_roles")
    op.drop_table("target_roles")
    op.drop_table("career_preferences")
