"""create post_votes table

Revision ID: 0007_create_post_votes
Revises: 0006_create_community_members
Create Date: 2026-09-02 15:35:01.811087
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007_create_post_votes"
down_revision: Union[str, None] = "0006_create_community_members"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_votes",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column(
            "vote_type",
            sa.Enum("up", "down", name="vote_type_enum", create_constraint=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"]),
        sa.PrimaryKeyConstraint("user_id", "post_id"),
    )
    op.create_index("ix_post_votes_post_id", "post_votes", ["post_id"])
    op.create_index("ix_post_votes_user_id", "post_votes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_post_votes_user_id", table_name="post_votes")
    op.drop_index("ix_post_votes_post_id", table_name="post_votes")
    op.drop_table("post_votes")
    op.execute("DROP TYPE IF EXISTS vote_type_enum")