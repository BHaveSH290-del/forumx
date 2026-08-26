from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CommunityMember(Base):
    __tablename__ = "community_members"
    __table_args__ = (
        PrimaryKeyConstraint(
            "user_id",
            "community_id",
            name="pk_community_members",
        ),
        UniqueConstraint(
            "user_id",
            "community_id",
            name="uq_community_members_user_id_community_id",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True,
    )
    community_id: Mapped[int] = mapped_column(
        ForeignKey("communities.id"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user = relationship("User")
    community = relationship("Community")
