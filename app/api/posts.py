from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db_session
from app.models import Community, CommunityMember, Post, PostVote, User, VoteType
from app.schemas.post import PostCreate, PostRead, PostUpdate


router = APIRouter(tags=["posts"])


class SortOrder(str, Enum):
    NEWEST = "newest"
    OLDEST = "oldest"
    POPULAR = "popular"


@router.post(
    "/communities/{community_id}/posts",
    response_model=PostRead,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    community_id: int,
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Post:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    is_creator = community.creator_id == current_user.id
    is_member = False
    if not is_creator:
        existing_membership = db.get(
            CommunityMember,
            {"user_id": current_user.id, "community_id": community.id},
        )
        is_member = existing_membership is not None

    if not (is_creator or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member or creator of this community to post.",
        )

    post = Post(
        title=post_in.title,
        content=post_in.content,
        author_id=current_user.id,
        community_id=community.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def _get_vote_counts_subquery():
    return (
        select(
            PostVote.post_id,
            func.count(case((PostVote.vote_type == VoteType.UP, 1))).label("upvote_count"),
            func.count(case((PostVote.vote_type == VoteType.DOWN, 1))).label("downvote_count"),
        )
        .group_by(PostVote.post_id)
        .subquery()
    )


@router.get("/communities/{community_id}/posts", response_model=list[PostRead])
def list_community_posts(
    community_id: int,
    sort: SortOrder = Query(default=SortOrder.NEWEST),
    db: Session = Depends(get_db_session),
) -> list[Post]:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    vote_counts = _get_vote_counts_subquery()

    base_query = (
        select(
            Post,
            func.coalesce(vote_counts.c.upvote_count, 0).label("upvote_count"),
            func.coalesce(vote_counts.c.downvote_count, 0).label("downvote_count"),
        )
        .outerjoin(vote_counts, Post.id == vote_counts.c.post_id)
        .where(Post.community_id == community_id)
    )

    if sort == SortOrder.POPULAR:
        score_expr = (
            func.coalesce(vote_counts.c.upvote_count, 0)
            - func.coalesce(vote_counts.c.downvote_count, 0)
        )
        query = base_query.order_by(score_expr.desc(), Post.created_at.desc(), Post.id.desc())
    elif sort == SortOrder.NEWEST:
        query = base_query.order_by(Post.created_at.desc(), Post.id.desc())
    else:  # SortOrder.OLDEST
        query = base_query.order_by(Post.created_at.asc(), Post.id.asc())

    results = db.execute(query).all()

    posts = []
    for post, upvote_count, downvote_count in results:
        post.upvote_count = upvote_count
        post.downvote_count = downvote_count
        post.score = upvote_count - downvote_count
        posts.append(post)

    return posts


@router.get("/posts/{post_id}", response_model=PostRead)
def get_post(
    post_id: int,
    db: Session = Depends(get_db_session),
) -> Post:
    vote_counts = _get_vote_counts_subquery()

    result = db.execute(
        select(
            Post,
            func.coalesce(vote_counts.c.upvote_count, 0).label("upvote_count"),
            func.coalesce(vote_counts.c.downvote_count, 0).label("downvote_count"),
        )
        .outerjoin(vote_counts, Post.id == vote_counts.c.post_id)
        .where(Post.id == post_id)
    ).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    post, upvote_count, downvote_count = result
    post.upvote_count = upvote_count
    post.downvote_count = downvote_count
    post.score = upvote_count - downvote_count

    return post


@router.patch("/posts/{post_id}", response_model=PostRead)
def update_post(
    post_id: int,
    post_in: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Post:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    if current_user.id != post.author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this post.",
        )

    if post_in.title is not None:
        post.title = post_in.title
    if post_in.content is not None:
        post.content = post_in.content
    post.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(post)
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
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

    if current_user.id != post.author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this post.",
        )

    db.delete(post)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Post cannot be deleted while it has comments.",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
