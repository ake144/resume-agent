"""add durable match results

Revision ID: 5d8e0f1a2b13
Revises: 4c7d9e0f1a12
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5d8e0f1a2b13"
down_revision: Union[str, Sequence[str], None] = "4c7d9e0f1a12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("job_posting_id", sa.UUID(), nullable=False),
        sa.Column("matcher_version", sa.String(length=50), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("confidence_level", sa.String(length=20), nullable=False),
        sa.Column("preference_alignment", sa.String(length=40), nullable=False),
        sa.Column("strong_matches", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("skill_gaps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tailoring_recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("hard_constraints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_match_results_user_id", "match_results", ["user_id"])
    op.create_index("ix_match_results_job_posting_id", "match_results", ["job_posting_id"])
    op.create_index("ix_match_results_user_id_created_at", "match_results", ["user_id", "created_at"])
    op.create_index(
        "ix_match_results_job_posting_id_created_at",
        "match_results",
        ["job_posting_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_match_results_job_posting_id_created_at", table_name="match_results")
    op.drop_index("ix_match_results_user_id_created_at", table_name="match_results")
    op.drop_index("ix_match_results_job_posting_id", table_name="match_results")
    op.drop_index("ix_match_results_user_id", table_name="match_results")
    op.drop_table("match_results")
