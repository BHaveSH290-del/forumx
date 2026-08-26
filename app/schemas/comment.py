from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    model_config = {"extra": "forbid", "str_strip_whitespace": True}


class CommentRead(BaseModel):
    id: int
    content: str
    author_id: int
    post_id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    model_config = {"extra": "forbid", "str_strip_whitespace": True}
