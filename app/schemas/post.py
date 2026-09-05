from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=5000)

    model_config = {"extra": "forbid", "str_strip_whitespace": True}


class PostRead(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    community_id: int
    created_at: datetime
    updated_at: datetime | None
    upvote_count: int = 0
    downvote_count: int = 0
    score: int = 0

    model_config = {"from_attributes": True}


class PaginatedPostResponse(BaseModel):
    items: list[PostRead]
    page: int
    limit: int
    has_next: bool

    model_config = {"from_attributes": True}


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=5000)

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    @model_validator(mode="after")
    def validate_has_changes(self) -> "PostUpdate":
        if self.title is None and self.content is None:
            raise ValueError("At least one field must be provided.")
        return self
