from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.models import Community, Post, PostVote, VoteType
from app.schemas.post import PaginatedPostResponse
from app.schemas.community import CommunityRead

router = APIRouter(tags=["frontpage"])


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


class SortOrder(str):
    NEWEST = "newest"
    OLDEST = "oldest"
    POPULAR = "popular"


@router.get("/f/{slug}", status_code=status.HTTP_200_OK)
def get_community_page(
    slug: str,
    sort: str = Query(default="newest", pattern="^(newest|oldest|popular)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> dict:
    # Case-insensitive lookup for community
    community = db.execute(
        select(Community).where(func.lower(Community.slug) == func.lower(slug))
    ).scalar_one_or_none()

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
        .where(Post.community_id == community.id)
    )

    if sort == "popular":
        score_expr = (
            func.coalesce(vote_counts.c.upvote_count, 0)
            - func.coalesce(vote_counts.c.downvote_count, 0)
        )
        query = base_query.order_by(score_expr.desc(), Post.created_at.desc(), Post.id.desc())
    elif sort == "newest":
        query = base_query.order_by(Post.created_at.desc(), Post.id.desc())
    else:  # oldest
        query = base_query.order_by(Post.created_at.asc(), Post.id.asc())

    offset = (page - 1) * limit
    query = query.limit(limit + 1).offset(offset)

    results = db.execute(query).all()

    posts = []
    for post, upvote_count, downvote_count in results:
        post.upvote_count = upvote_count
        post.downvote_count = downvote_count
        post.score = upvote_count - downvote_count
        posts.append(post)

    has_next = len(posts) > limit
    if has_next:
        posts = posts[:limit]

    paginated_posts = PaginatedPostResponse(
        items=posts,
        page=page,
        limit=limit,
        has_next=has_next,
    )

    return {
        "community": CommunityRead.model_validate(community),
        "posts": paginated_posts,
    }