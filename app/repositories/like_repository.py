from sqlalchemy.orm import Session
from sqlalchemy import func, exists
from app.models.like import Like

def count_likes_for_post(db: Session, post_id: int) -> int:
    return (
        db.query(func.count(Like.id))
        .filter(Like.post_id == post_id)
        .scalar()
    )

def is_post_liked_by_user(
    db: Session,
    post_id: int,
    user_id: int
) -> bool:
    return db.query(
        exists().where(
            Like.post_id == post_id,
            Like.user_id == user_id
        )
    ).scalar()
