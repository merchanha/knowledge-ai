"""Add casbin_rule table for PyCasbin policies.

Revision ID: 20260606_0001
Revises: 6bbd20292723
Create Date: 2026-06-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260606_0001"
down_revision: str | Sequence[str] | None = "6bbd20292723"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "casbin_rule",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ptype", sa.String(length=255), nullable=True),
        sa.Column("v0", sa.String(length=255), nullable=True),
        sa.Column("v1", sa.String(length=255), nullable=True),
        sa.Column("v2", sa.String(length=255), nullable=True),
        sa.Column("v3", sa.String(length=255), nullable=True),
        sa.Column("v4", sa.String(length=255), nullable=True),
        sa.Column("v5", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("casbin_rule")
