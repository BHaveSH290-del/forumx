from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db_session
from app.models import Community, CommunityMember, User
from app.schemas.membership import (
    CommunityMemberRead,
    CommunityMembershipStatus,
    MembershipRead,
    MembershipRequest,
)


router = APIRouter(prefix="/communities", tags=["memberships"])


@router.post(
    "/{community_id}/join",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
)
def join_community(
    community_id: int,
    _membership_in: MembershipRequest | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> CommunityMember:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    existing_membership = db.get(
        CommunityMember,
        {"user_id": current_user.id, "community_id": community.id},
    )
    if existing_membership is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already a member of this community.",
        )

    membership = CommunityMember(
        user_id=current_user.id,
        community_id=community.id,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@router.delete(
    "/{community_id}/join",
    status_code=status.HTTP_204_NO_CONTENT,
)
def leave_community(
    community_id: int,
    _membership_in: MembershipRequest | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Response:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    membership = db.get(
        CommunityMember,
        {"user_id": current_user.id, "community_id": community.id},
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found.",
        )

    db.delete(membership)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{community_id}/members",
    response_model=list[CommunityMemberRead],
)
def list_community_members(
    community_id: int,
    db: Session = Depends(get_db_session),
) -> list[User]:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    members = db.scalars(
        select(User)
        .join(CommunityMember, CommunityMember.user_id == User.id)
        .where(CommunityMember.community_id == community.id)
        .order_by(User.id)
    ).all()
    return list(members)


@router.get(
    "/{community_id}/membership",
    response_model=CommunityMembershipStatus,
)
def get_community_membership_status(
    community_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> dict[str, bool]:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    is_creator = community.creator_id == current_user.id
    membership = db.get(
        CommunityMember,
        {"user_id": current_user.id, "community_id": community.id},
    )
    is_member = membership is not None

    return {
        "is_member": is_member,
        "is_creator": is_creator,
    }

