"""add community slug

Revision ID: 0008_add_community_slug
Revises: 0007_create_post_votes
Create Date: 2026-09-02 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import re


# revision identifiers, used by Alembic.
revision: str = "0008_add_community_slug"
down_revision: Union[str, None] = "0007_create_post_votes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    slug = name.lower().replace(" ", "-").replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:50]


def upgrade() -> None:
    # Add slug column as nullable first
    op.add_column(
        "communities",
        sa.Column("slug", sa.String(length=50), nullable=True),
    )

    # Populate slug for existing communities
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, name FROM communities"))
    for row in result:
        base_slug = generate_slug(row.name)
        slug = base_slug
        # Handle duplicates by appending a number
        counter = 1
        while True:
            existing = conn.execute(
                sa.text("SELECT 1 FROM communities WHERE lower(slug) = lower(:slug) AND id != :id"),
                {"slug": slug, "id": row.id}
            ).scalar()
            if not existing:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        conn.execute(
            sa.text("UPDATE communities SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": row.id}
        )

    # Now make slug NOT NULL
    op.alter_column("communities", "slug", nullable=False)

    # Create case-insensitive unique index on slug
    op.create_index("uq_communities_slug_lower", "communities", [sa.text("lower(slug)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_communities_slug_lower", table_name="communities")
    op.drop_column("communities", "slug")