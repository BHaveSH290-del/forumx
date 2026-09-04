from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db_session
from app.models import Post, PostVote, User
from app.schemas.vote import VoteCreate

router = APIRouter(tags=["votes"])


@router.post(
    "/posts/{post_id}/vote",
    status_code=status.HTTP_201_CREATED,
)
def vote_post(
    post_id: int,
    vote_in: VoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> dict:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    existing_vote = db.get(PostVote, {"user_id": current_user.id, "post_id": post_id})

    if existing_vote is None:
        new_vote = PostVote(
            user_id=current_user.id,
            post_id=post_id,
            vote_type=vote_in.vote_type,
        )
        db.add(new_vote)
        db.commit()
        return {"detail": "Vote created."}

    if existing_vote.vote_type == vote_in.vote_type:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already voted on this post.",
        )

    existing_vote.vote_type = vote_in.vote_type
    db.commit()
    return {"detail": "Vote updated."}


@router.delete(
    "/posts/{post_id}/vote",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_vote(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Response:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    existing_vote = db.get(PostVote, {"user_id": current_user.id, "post_id": post_id})

    if existing_vote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vote not found.",
        )

    db.delete(existing_vote)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)