"""add post search index

Revision ID: 0009_add_post_search_index
Revises: 0008_add_community_slug
Create Date: 2026-09-02 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0009_add_post_search_index"
down_revision: Union[str, None] = "0008_add_community_slug"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create GIN index for full-text search on title and content
    # Using weights: A for title (highest), B for content
    # Use tsvector_concat for proper tsvector concatenation
    op.execute("""
        CREATE INDEX ix_posts_search_vector ON posts USING GIN (
            tsvector_concat(
                setweight(to_tsvector('english', coalesce(title, '')), 'A'),
                setweight(to_tsvector('english', coalesce(content, '')), 'B')
            )
        )
    """)


def downgrade() -> None:
    op.drop_index("ix_posts_search_vector", table_name="posts")