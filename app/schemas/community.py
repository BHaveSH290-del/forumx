import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")
SLUG_MAX_LENGTH = 50


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    slug = name.lower().replace(" ", "-").replace("_", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:SLUG_MAX_LENGTH]


class CommunityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=500)
    slug: str | None = Field(default=None, min_length=1, max_length=SLUG_MAX_LENGTH)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not SLUG_PATTERN.match(v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens.")
        return v

    @model_validator(mode="after")
    def generate_slug_if_missing(self) -> "CommunityCreate":
        if self.slug is None:
            self.slug = generate_slug(self.name)
        return self


class CommunityRead(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    creator_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
