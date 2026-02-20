from sqlalchemy.orm import Session
from sqlalchemy import func, exists
from app.models.like import Like

class LikeRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_likes_for_post(self, post_id: int) -> int:
        return (
            self.db.query(func.count(Like.id))
            .filter(Like.post_id == post_id)
            .scalar()
        )

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

    def count_by_post(self, post_id: int):
        return self.db.query(Like).filter(Like.post_id == post_id).count()

    def create(self, post_id: int, user_id: int):
        like = Like(user_id=user_id, post_id=post_id)
        self.db.add(like)
        self.db.commit()
        return like

    def delete(self, like: Like):
        self.db.delete(like)
        self.db.commit()

# Compatibilidad con código actual hasta que refactoricemos el router usando el Injection Dependency
def count_likes_for_post(db: Session, post_id: int) -> int:
    return LikeRepository(db).count_likes_for_post(post_id)

def is_post_liked_by_user(db: Session, post_id: int, user_id: int) -> bool:
    return LikeRepository(db).is_post_liked_by_user(post_id, user_id)
