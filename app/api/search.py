from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, case, text, cast
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.models import Post, PostVote, VoteType
from app.schemas.post import PaginatedPostResponse

router = APIRouter(tags=["search"])


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


@router.get("/search/posts", response_model=PaginatedPostResponse)
def search_posts(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> PaginatedPostResponse:
    # Trim whitespace
    query_text = q.strip()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Search query cannot be empty.",
        )

    # Build the search query using websearch_to_tsquery for user-friendly syntax
    # This allows queries like "python -snake" (exclude), "python programming" (phrase), etc.
    search_query = func.websearch_to_tsquery('english', query_text)

    # Build the search vector matching the index expression
    # Use text() with proper PostgreSQL "char" type (quoted) for setweight
    search_vector = func.tsvector_concat(
        func.setweight(func.to_tsvector('english', func.coalesce(Post.title, '')), text("'A'::\"char\"")),
        func.setweight(func.to_tsvector('english', func.coalesce(Post.content, '')), text("'B'::\"char\"")),
    )

    # Calculate relevance rank
    rank = func.ts_rank(search_vector, search_query)

    vote_counts = _get_vote_counts_subquery()

    base_query = (
        select(
            Post,
            func.coalesce(vote_counts.c.upvote_count, 0).label("upvote_count"),
            func.coalesce(vote_counts.c.downvote_count, 0).label("downvote_count"),
            rank.label("search_rank"),
        )
        .outerjoin(vote_counts, Post.id == vote_counts.c.post_id)
        .where(search_vector.op("@@")(search_query))
        .order_by(rank.desc(), Post.created_at.desc(), Post.id.desc())
    )

    offset = (page - 1) * limit
    query = base_query.limit(limit + 1).offset(offset)

    results = db.execute(query).all()

    posts = []
    for post, upvote_count, downvote_count, _search_rank in results:
        post.upvote_count = upvote_count
        post.downvote_count = downvote_count
        post.score = upvote_count - downvote_count
        posts.append(post)

    has_next = len(posts) > limit
    if has_next:
        posts = posts[:limit]

    return PaginatedPostResponse(
        items=posts,
        page=page,
        limit=limit,
        has_next=has_next,
    )