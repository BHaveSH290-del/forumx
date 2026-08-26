"""create community members table

Revision ID: 0006_create_community_members
Revises: 0005_add_updated_at
Create Date: 2026-08-26 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_create_community_members"
down_revision: Union[str, None] = "0005_add_updated_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "community_members",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"]),
        sa.PrimaryKeyConstraint("user_id", "community_id"),
        sa.UniqueConstraint(
            "user_id",
            "community_id",
            name="uq_community_members_user_id_community_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("community_members")
