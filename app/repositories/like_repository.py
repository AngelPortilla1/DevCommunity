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
        self.db.commit()
        return like

    def delete(self, like: Like):
        self.db.delete(like)
        self.db.commit()

    def get_liked_post_ids(self, user_id: int, post_ids: list[int]):
        results = (
            self.db.query(Like.post_id)
            .filter(
                Like.user_id == user_id,
                Like.post_id.in_(post_ids)
            )
            .all()
        )
        return {r[0] for r in results}

# Compatibilidad con código actual hasta que refactoricemos el router usando el Injection Dependency


def is_post_liked_by_user(db: Session, post_id: int, user_id: int) -> bool:
    return LikeRepository(db).is_post_liked_by_user(post_id, user_id)
