"""Add directories table for hierarchical project trees.

Revision ID: 20260613_0001
Revises: 20260606_0001
Create Date: 2026-06-13

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260613_0001"
down_revision: str | Sequence[str] | None = "20260606_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "directories",
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
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["directories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "parent_id",
            "name",
            name="uq_directories_project_parent_name",
        ),
    )
    op.create_index(
        op.f("ix_directories_parent_id"),
        "directories",
        ["parent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_directories_project_id"),
        "directories",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_directories_project_root",
        "directories",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_directories_project_root", table_name="directories")
    op.drop_index(op.f("ix_directories_project_id"), table_name="directories")
    op.drop_index(op.f("ix_directories_parent_id"), table_name="directories")
    op.drop_table("directories")
