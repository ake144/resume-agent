"""add resume snapshot to match results

Revision ID: 9a4e7b2c6d11
Revises: 6e9f1a2b3c14
Create Date: 2026-10-14 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a4e7b2c6d11"
down_revision: Union[str, Sequence[str], None] = "6e9f1a2b3c14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("match_results", sa.Column("resume_version_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_match_results_resume_version_id_resume_versions",
        "match_results",
        "resume_versions",
        ["resume_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_match_results_resume_version_id", "match_results", ["resume_version_id"])


def downgrade() -> None:
    op.drop_index("ix_match_results_resume_version_id", table_name="match_results")
    op.drop_constraint("fk_match_results_resume_version_id_resume_versions", "match_results", type_="foreignkey")
    op.drop_column("match_results", "resume_version_id")
