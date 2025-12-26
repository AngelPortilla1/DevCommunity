from app.models.post import Post
from app.models.user import User
from app.schemas import PostResponse


def map_post_to_response(
    post: Post,
    current_user: User | None = None
) -> PostResponse:
    likes_count = len(post.likes)

    liked_by_me = False
    if current_user:
        liked_by_me = any(
            like.user_id == current_user.id
            for like in post.likes
        )

    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        author=post.author,
        likes_count=likes_count,
        liked_by_me=liked_by_me,
        created_at=post.created_at,
        updated_at=post.updated_at
    )
