from datetime import datetime

from pydantic import BaseModel


class MembershipRequest(BaseModel):
    model_config = {"extra": "forbid"}


class MembershipRead(BaseModel):
    user_id: int
    community_id: int
    joined_at: datetime

    model_config = {"from_attributes": True}


class CommunityMemberRead(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}


class CommunityMembershipStatus(BaseModel):
    is_member: bool
    is_creator: bool

