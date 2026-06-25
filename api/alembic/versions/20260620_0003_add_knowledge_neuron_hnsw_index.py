"""Add HNSW index for cosine similarity search on knowledge_neurons.embedding.

Revision ID: 20260620_0003
Revises: 20260620_0002
Create Date: 2026-06-20

"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260620_0003"
down_revision: str | Sequence[str] | None = "20260620_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX ix_knowledge_neurons_embedding_hnsw
        ON knowledge_neurons
        USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_neurons_embedding_hnsw", table_name="knowledge_neurons")
