from sqlalchemy.orm import Session
from app.models.coments import Comment

class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, comment_id: int):
        return self.db.query(Comment).filter(Comment.id == comment_id).first()

    def get_by_post_id(self, post_id: int):
        return self.db.query(Comment).filter(Comment.post_id == post_id).all()

    def create(self, content: str, author_id: int, post_id: int):
        new_comment = Comment(
            content=content,
            author_id=author_id,
            post_id=post_id
        )
        self.db.add(new_comment)
        self.db.commit()
        self.db.refresh(new_comment)
        return new_comment

    def update(self, comment: Comment, content: str):
        comment.content = content
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete(self, comment: Comment):
        self.db.delete(comment)
        self.db.commit()
