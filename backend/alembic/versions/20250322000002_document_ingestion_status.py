"""Add ingestion tracking columns to document_sources."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250322000002"
down_revision: Union[str, None] = "20250322000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ingestion status columns."""
    op.add_column(
        "document_sources",
        sa.Column("ingestion_status", sa.String(length=32), nullable=False, server_default="pending"),
    )
    op.add_column("document_sources", sa.Column("last_error", sa.Text(), nullable=True))
    op.alter_column("document_sources", "ingestion_status", server_default=None)


def downgrade() -> None:
    """Remove ingestion status columns."""
    op.drop_column("document_sources", "last_error")
    op.drop_column("document_sources", "ingestion_status")
