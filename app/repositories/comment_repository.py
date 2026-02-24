from sqlalchemy.orm import Session
from app.models.comment import Comment
from app.models.post import Post

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
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po:
            po.comments_count += 1
            
        self.db.commit()
        self.db.refresh(new_comment)
        return new_comment

    def update(self, comment: Comment, content: str):
        comment.content = content
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete(self, comment: Comment):
        post_id = comment.post_id
        self.db.delete(comment)
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po and po.comments_count > 0:
            po.comments_count -= 1
            
        self.db.commit()
