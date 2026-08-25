from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db_session
from app.models import Community, User
from app.schemas.community import CommunityCreate, CommunityRead


router = APIRouter(prefix="/communities", tags=["communities"])


@router.post("", response_model=CommunityRead, status_code=status.HTTP_201_CREATED)
def create_community(
    community_in: CommunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Community:
    community = Community(
        name=community_in.name,
        description=community_in.description,
        creator_id=current_user.id,
    )

    db.add(community)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        constraint_name = getattr(exc.orig, "diag", None)
        constraint_name = getattr(constraint_name, "constraint_name", "")

        if constraint_name == "uq_communities_name":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Community name already exists.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create community.",
        ) from exc

    db.refresh(community)
    return community


@router.get("", response_model=list[CommunityRead])
def list_communities(db: Session = Depends(get_db_session)) -> list[Community]:
    communities = db.scalars(select(Community).order_by(Community.id)).all()
    return list(communities)


@router.get("/{community_id}", response_model=CommunityRead)
def get_community(
    community_id: int,
    db: Session = Depends(get_db_session),
) -> Community:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    return community
