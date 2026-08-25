"""create communities table

Revision ID: 0002_create_communities_table
Revises: 0001_create_users_table
Create Date: 2026-08-25 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_create_communities_table"
down_revision: Union[str, None] = "0001_create_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "communities",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"]),
    )
    op.create_unique_constraint("uq_communities_name", "communities", ["name"])


def downgrade() -> None:
    op.drop_constraint("uq_communities_name", "communities", type_="unique")
    op.drop_table("communities")
