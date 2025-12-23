from app.schemas import CommentResponse, UserPublicResponse
from app.models import Comment

def map_comment_to_response(comment: Comment):
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        author=UserPublicResponse(
            id=comment.author.id,
            username=comment.author.username,
            email=comment.author.email
        ),
        post_id=comment.post_id,
        created_at=comment.created_at
    )
