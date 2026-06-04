"""add project_memberships table

Revision ID: 6bbd20292723
Revises: 20260531_0001
Create Date: 2026-06-03 18:16:57.403795

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "6bbd20292723"
down_revision: str | Sequence[str] | None = "20260531_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

project_membership_role_enum = postgresql.ENUM(
    "owner",
    "member",
    name="project_membership_role",
    create_type=False,
)


def upgrade() -> None:
    # A failed prior run may have left project_membership_role with wrong labels
    # (e.g. OWNER/MEMBER). Drop and recreate; table does not exist yet.
    op.execute("DROP TYPE IF EXISTS project_membership_role")
    op.execute("CREATE TYPE project_membership_role AS ENUM ('owner', 'member')")

    op.create_table(
        "project_memberships",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("role", project_membership_role_enum, nullable=False, server_default="member"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "project_id", name="uq_project_memberships_user_project"),
    )
    op.create_index(
        op.f("ix_project_memberships_project_id"),
        "project_memberships",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_memberships_user_id"),
        "project_memberships",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_project_memberships_user_id"), table_name="project_memberships")
    op.drop_index(op.f("ix_project_memberships_project_id"), table_name="project_memberships")
    op.drop_table("project_memberships")
    project_membership_role_enum.drop(op.get_bind(), checkfirst=True)
