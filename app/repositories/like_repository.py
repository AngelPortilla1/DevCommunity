from sqlalchemy.orm import Session
from sqlalchemy import func, exists
from app.models.like import Like
from app.models.post import Post

class LikeRepository:
    def __init__(self, db: Session):
        self.db = db



    def is_post_liked_by_user(self, post_id: int, user_id: int) -> bool:
        return self.db.query(
            exists().where(
                Like.post_id == post_id,
                Like.user_id == user_id
            )
        ).scalar()
        
    def get_like(self, post_id: int, user_id: int):
        return self.db.query(Like).filter(
            Like.post_id == post_id,
            Like.user_id == user_id
        ).first()



    def create(self, post_id: int, user_id: int):
        like = Like(user_id=user_id, post_id=post_id)
        self.db.add(like)
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po:
            po.likes_count += 1
            
        self.db.commit()
        return like

    def delete(self, like: Like):
        post_id = like.post_id
        self.db.delete(like)
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po and po.likes_count > 0:
            po.likes_count -= 1
            
        self.db.commit()

# Compatibilidad con código actual hasta que refactoricemos el router usando el Injection Dependency


def is_post_liked_by_user(db: Session, post_id: int, user_id: int) -> bool:
    return LikeRepository(db).is_post_liked_by_user(post_id, user_id)
