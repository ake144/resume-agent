"""add transparent interview answer score"""
from alembic import op
import sqlalchemy as sa
revision="ee5a1c6b9042"; down_revision="d1f6b3e8a207"; branch_labels=depends_on=None
def upgrade(): op.add_column("interview_answers", sa.Column("rubric_score", sa.Integer(), nullable=True))
def downgrade(): op.drop_column("interview_answers", "rubric_score")
