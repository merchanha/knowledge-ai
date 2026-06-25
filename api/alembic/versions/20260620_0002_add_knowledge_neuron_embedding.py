"""Add pgvector embedding column to knowledge_neurons.

Revision ID: 20260620_0002
Revises: 20260620_0001
Create Date: 2026-06-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "20260620_0002"
down_revision: str | Sequence[str] | None = "20260620_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "knowledge_neurons",
        sa.Column("embedding", Vector(1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("knowledge_neurons", "embedding")
