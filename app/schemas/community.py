from datetime import datetime

from pydantic import BaseModel, Field


class CommunityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=500)


class CommunityRead(BaseModel):
    id: int
    name: str
    description: str
    creator_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
