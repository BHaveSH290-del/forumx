import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class VoteType(str, enum.Enum):
    UP = "up"
    DOWN = "down"


class PostVote(Base):
    __tablename__ = "post_votes"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), primary_key=True, nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id"), primary_key=True, nullable=False
    )
    vote_type: Mapped[VoteType] = mapped_column(
        Enum(
            VoteType,
            name="vote_type_enum",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )