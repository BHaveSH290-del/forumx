from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db_session
from app.models import Comment, Post, User
from app.schemas.comment import CommentCreate, CommentRead


router = APIRouter(tags=["comments"])


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Comment:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    comment = Comment(
        content=comment_in.content,
        author_id=current_user.id,
        post_id=post.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/posts/{post_id}/comments", response_model=list[CommentRead])
def list_post_comments(
    post_id: int,
    db: Session = Depends(get_db_session),
) -> list[Comment]:
    post = db.get(Post, post_id)

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    comments = db.scalars(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.id)
    ).all()
    return list(comments)


@router.get("/comments/{comment_id}", response_model=CommentRead)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db_session),
) -> Comment:
    comment = db.get(Comment, comment_id)

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    return comment
