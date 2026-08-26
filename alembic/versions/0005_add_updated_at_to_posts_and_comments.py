"""add updated_at to posts and comments

Revision ID: 0005_add_updated_at
Revises: 0004_create_comments_table
Create Date: 2026-08-26 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_add_updated_at"
down_revision: Union[str, None] = "0004_create_comments_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "posts",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "comments",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("comments", "updated_at")
    op.drop_column("posts", "updated_at")
