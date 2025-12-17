from app.models.post import Post
from app.models.user import User

def map_post_to_response(post: Post, current_user: User) -> dict:
    likes_count = len(post.likes)
    liked_by_me = any(
        like.user_id == current_user.id
        for like in post.likes
    )

    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "author": post.author,
        "likes_count": likes_count,
        "liked_by_me": liked_by_me,
    }
