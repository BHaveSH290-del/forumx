from datetime import datetime

from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)

    model_config = {"extra": "forbid"}


class PostRead(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    community_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
