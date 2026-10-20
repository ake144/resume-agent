"""add application pipeline events"""
from alembic import op
import sqlalchemy as sa
revision = "c2a6f8b9d301"
down_revision = "a8c3d1e5f902"
branch_labels = depends_on = None
def upgrade():
    op.create_table("application_events", sa.Column("id", sa.UUID(), primary_key=True), sa.Column("user_id", sa.UUID(), nullable=False), sa.Column("application_id", sa.UUID(), nullable=False), sa.Column("event_type", sa.String(40), nullable=False), sa.Column("from_status", sa.String(20)), sa.Column("to_status", sa.String(20)), sa.Column("note", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"))
    op.create_index("ix_application_events_user_id", "application_events", ["user_id"])
    op.create_index("ix_application_events_application_id", "application_events", ["application_id"])
    op.create_index("ix_application_events_application_created", "application_events", ["application_id", "created_at"])
def downgrade():
    op.drop_table("application_events")
