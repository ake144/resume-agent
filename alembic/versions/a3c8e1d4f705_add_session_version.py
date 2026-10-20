"""add server-side session invalidation version"""
from alembic import op
import sqlalchemy as sa
revision="a3c8e1d4f705"; down_revision="ee5a1c6b9042"; branch_labels=depends_on=None
def upgrade():
    op.add_column("users", sa.Column("session_version", sa.Integer(), server_default="0", nullable=False))
def downgrade(): op.drop_column("users", "session_version")
