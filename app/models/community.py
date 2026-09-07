from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    creator = relationship("User")

    __table_args__ = (
        Index("ix_communities_slug_lower", "slug", postgresql_ops={"slug": "text_pattern_ops"}),
    )
