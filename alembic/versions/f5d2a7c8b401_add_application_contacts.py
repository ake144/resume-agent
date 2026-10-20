"""add application contacts"""
from alembic import op
import sqlalchemy as sa
revision="f5d2a7c8b401"; down_revision="e4b9c2d7a115"; branch_labels=depends_on=None
def upgrade():
 op.create_table("application_contacts",sa.Column("id",sa.UUID(),primary_key=True),sa.Column("user_id",sa.UUID(),nullable=False),sa.Column("application_id",sa.UUID(),nullable=False),sa.Column("name",sa.String(255),nullable=False),sa.Column("email",sa.String(255)),sa.Column("role",sa.String(255)),sa.Column("notes",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["application_id"],["applications.id"],ondelete="CASCADE"))
def downgrade(): op.drop_table("application_contacts")
