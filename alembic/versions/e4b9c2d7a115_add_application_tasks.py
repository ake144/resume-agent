"""add application follow-up tasks"""
from alembic import op
import sqlalchemy as sa
revision="e4b9c2d7a115"; down_revision="c2a6f8b9d301"; branch_labels=depends_on=None
def upgrade():
 op.create_table("application_tasks",sa.Column("id",sa.UUID(),primary_key=True),sa.Column("user_id",sa.UUID(),nullable=False),sa.Column("application_id",sa.UUID(),nullable=False),sa.Column("title",sa.String(255),nullable=False),sa.Column("note",sa.Text()),sa.Column("due_at",sa.DateTime(timezone=True)),sa.Column("completed_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["application_id"],["applications.id"],ondelete="CASCADE"));op.create_index("ix_application_tasks_user_due","application_tasks",["user_id","due_at"])
def downgrade(): op.drop_table("application_tasks")
