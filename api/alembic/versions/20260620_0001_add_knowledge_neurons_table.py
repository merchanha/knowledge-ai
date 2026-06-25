"""Add knowledge_neurons table for stored knowledge documents.

Revision ID: 20260620_0001
Revises: 20260613_0001
Create Date: 2026-06-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260620_0001"
down_revision: str | Sequence[str] | None = "20260613_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_neurons",
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
        sa.Column("directory_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["directory_id"], ["directories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_neurons_directory_id"),
        "knowledge_neurons",
        ["directory_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_neurons_directory_id"), table_name="knowledge_neurons")
    op.drop_table("knowledge_neurons")
