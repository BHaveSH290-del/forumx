from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db_session
from app.models import Community, Post, User
from app.schemas.post import PostCreate, PostRead, PostUpdate


router = APIRouter(tags=["posts"])


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


@router.get("/communities/{community_id}/posts", response_model=list[PostRead])
def list_community_posts(
    community_id: int,
    db: Session = Depends(get_db_session),
) -> list[Post]:
    community = db.get(Community, community_id)

    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found.",
        )

    posts = db.scalars(
        select(Post)
        .where(Post.community_id == community_id)
        .order_by(Post.id)
    ).all()
    return list(posts)


@router.get("/posts/{post_id}", response_model=PostRead)
def get_post(
    post_id: int,
    db: Session = Depends(get_db_session),
) -> Post:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

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
