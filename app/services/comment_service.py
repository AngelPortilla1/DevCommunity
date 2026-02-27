from sqlalchemy.orm import Session
from app.repositories.comment_repository import CommentRepository
from app.models.post import Post
from app.models.user import User
from app.exceptions.comment_exceptions import CommentNotFound, ForbiddenCommentAction
from app.exceptions.post_exceptions import PostNotFound
from app.schemas import CommentCreate, CommentUpdate

class CommentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CommentRepository(db)

    def create_comment(self, post_id: int, comment_data: CommentCreate, current_user: User):
        # Validar si el post existe. Lo hacemos a través del db central (o podríamos tener un PostRepository)
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise PostNotFound()
        
        new_comment = self.repository.create(
            content=comment_data.content,
            author_id=current_user.id,
            post_id=post_id
        )
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po:
            po.comments_count += 1
            self.db.commit()
            
        return new_comment

    def get_comments_by_post(self, post_id: int):
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise PostNotFound()
        return self.repository.get_by_post_id(post_id)

    def update_comment(self, comment_id: int, comment_data: CommentUpdate, current_user: User):
        comment = self.repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFound()
        
        if comment.author_id != current_user.id:
            raise ForbiddenCommentAction()
            
        return self.repository.update(comment, comment_data.content)

    def delete_comment(self, comment_id: int, current_user: User):
        comment = self.repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFound()
            
        if comment.author_id != current_user.id and current_user.role != 'admin':
            raise ForbiddenCommentAction()
            
        post_id = comment.post_id
        self.repository.delete(comment)
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po and po.comments_count > 0:
            po.comments_count -= 1
            self.db.commit()
