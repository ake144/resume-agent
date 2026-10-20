"""add user feedback"""
from alembic import op
import sqlalchemy as sa
revision="b7e4d9a1c602"; down_revision="f5d2a7c8b401"; branch_labels=depends_on=None
def upgrade(): op.create_table("user_feedback",sa.Column("id",sa.UUID(),primary_key=True),sa.Column("user_id",sa.UUID(),nullable=False),sa.Column("subject_type",sa.String(40),nullable=False),sa.Column("subject_id",sa.UUID(),nullable=False),sa.Column("rating",sa.Integer()),sa.Column("feedback_type",sa.String(40),nullable=False),sa.Column("comment",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="CASCADE"))
def downgrade(): op.drop_table("user_feedback")
