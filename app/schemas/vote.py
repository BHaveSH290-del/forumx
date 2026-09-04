from enum import Enum
from pydantic import BaseModel


class VoteType(str, Enum):
    UP = "up"
    DOWN = "down"


class VoteCreate(BaseModel):
    vote_type: VoteType

    model_config = {"extra": "forbid"}