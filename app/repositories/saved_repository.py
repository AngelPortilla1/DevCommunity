from sqlalchemy.orm import Session, selectinload
from sqlalchemy import exists
from app.models.saved_post import SavedPost
from app.models.post import Post


class SavedRepository:
    def __init__(self, db: Session):
        self.db = db

    def is_post_saved_by_user(self, post_id: int, user_id: int) -> bool:
        return self.db.query(
            exists().where(
                SavedPost.post_id == post_id,
                SavedPost.user_id == user_id
            )
        ).scalar()

    def get_saved(self, post_id: int, user_id: int) -> SavedPost | None:
        return self.db.query(SavedPost).filter(
            SavedPost.post_id == post_id,
            SavedPost.user_id == user_id
        ).first()

    def create(self, post_id: int, user_id: int) -> SavedPost:
        saved_post = SavedPost(user_id=user_id, post_id=post_id)
        self.db.add(saved_post)
        self.db.commit()
        self.db.refresh(saved_post)
        return saved_post

    def delete(self, saved_post: SavedPost) -> None:
        self.db.delete(saved_post)
        self.db.commit()

    def get_saved_posts_paginated(self, user_id: int, page: int, size: int) -> tuple[int, list[Post]]:
        query = (
            self.db.query(SavedPost)
            .filter(SavedPost.user_id == user_id)
            .options(
                selectinload(SavedPost.post).selectinload(Post.author)
            )
            .order_by(SavedPost.saved_at.desc())
        )
        total = query.count()
        saved_entries = query.offset((page - 1) * size).limit(size).all()
        posts = [entry.post for entry in saved_entries if entry.post is not None]
        return total, posts

    def get_saved_post_ids(self, user_id: int, post_ids: list[int]) -> set[int]:
        if not post_ids:
            return set()
        results = (
            self.db.query(SavedPost.post_id)
            .filter(
                SavedPost.user_id == user_id,
                SavedPost.post_id.in_(post_ids)
            )
            .all()
        )
        return {r[0] for r in results}
