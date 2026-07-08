"""Add is_context_exposed to project_memberships for MCP exposure control.

Revision ID: 20260704_0002
Revises: 20260704_0001
Create Date: 2026-07-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260704_0002"
down_revision: str | Sequence[str] | None = "20260704_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "project_memberships",
        sa.Column(
            "is_context_exposed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("project_memberships", "is_context_exposed")
