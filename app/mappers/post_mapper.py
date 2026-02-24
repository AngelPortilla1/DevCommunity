from app.models.post import Post

def map_post_to_response(
    post: Post,
    liked_by_me: bool
) -> dict:

    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "author": post.author,
        "likes_count": post.likes_count,
        "comments_count": post.comments_count,
        "liked_by_me": liked_by_me,
    }
