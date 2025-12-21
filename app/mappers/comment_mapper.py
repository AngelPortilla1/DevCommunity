from app.models.coments import Comment
from app.schemas import CommentResponse


def map_comment_to_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        author_id=comment.author_id,
        post_id=comment.post_id,
        created_at=comment.created_at
        
    )
