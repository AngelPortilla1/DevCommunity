from sqlalchemy.orm import Session
from app.repositories.saved_repository import SavedRepository
from app.repositories.like_repository import LikeRepository
from app.models.post import Post
from app.models.user import User
from app.exceptions.post_exceptions import PostNotFound
from app.exceptions.saved_exceptions import PostAlreadySaved, PostNotSaved
from app.mappers.post_mapper import map_post_to_response


class SavedService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SavedRepository(db)
        self.like_repository = LikeRepository(db)

    def save_post(self, post_id: int, current_user: User) -> dict:
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise PostNotFound()

        existing_saved = self.repository.get_saved(post_id, current_user.id)
        if existing_saved:
            raise PostAlreadySaved()

        self.repository.create(post_id, current_user.id)
        return {
            "saved": True,
            "message": "Post guardado correctamente"
        }

    def unsave_post(self, post_id: int, current_user: User) -> dict:
        saved_entry = self.repository.get_saved(post_id, current_user.id)
        if not saved_entry:
            raise PostNotSaved()

        self.repository.delete(saved_entry)
        return {
            "saved": False,
            "message": "Post eliminado de guardados"
        }

    def get_saved_posts(self, current_user: User, page: int = 1, size: int = 10) -> dict:
        total, posts = self.repository.get_saved_posts_paginated(
            user_id=current_user.id,
            page=page,
            size=size
        )

        post_ids = [post.id for post in posts]
        liked_ids = self.like_repository.get_liked_post_ids(
            user_id=current_user.id,
            post_ids=post_ids
        )

        items = [
            map_post_to_response(
                post,
                liked_by_me=post.id in liked_ids
            )
            for post in posts
        ]

        total_pages = (total + size - 1) // size if size > 0 else 0

        return {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "items": items
        }

    def check_saved(self, post_id: int, current_user: User) -> dict:
        is_saved = self.repository.is_post_saved_by_user(post_id, current_user.id)
        return {
            "is_saved": is_saved,
            "post_id": post_id
        }
