from sqlalchemy.orm import Session
from app.repositories.post_repository import PostRepository
from app.repositories.like_repository import LikeRepository
from app.models.user import User
from app.schemas import PostCreate
from app.exceptions.post_exceptions import PostNotFound, ForbiddenAction
from app.mappers.post_mapper import map_post_to_response
from datetime import date

class PostService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PostRepository(db)
        self.like_repository = LikeRepository(db)

    def create_post(self, post_data: PostCreate, current_user: User):
        new_post = self.repository.create(
            title=post_data.title,
            content=post_data.content,
            author_id=current_user.id
        )
        return map_post_to_response(new_post, likes_count=0, liked_by_me=False)

    def get_posts(
        self,
        page: int,
        limit: int,
        search: str | None,
        author_id: int | None,
        from_date: date | None,
        to_date: date | None,
        current_user: User
    ):
        filter_author_id = author_id
        if current_user.role != "admin":
            filter_author_id = current_user.id
            
        skip = (page - 1) * limit
        total, posts = self.repository.get_posts(
            skip=skip,
            limit=limit,
            search=search,
            author_id=filter_author_id,
            from_date=from_date,
            to_date=to_date
        )

        post_ids = [post.id for post in posts]
        likes_count_map = self.repository.get_likes_count_for_posts(post_ids)
        liked_post_ids = self.repository.get_user_liked_posts(post_ids, current_user.id)

        posts_data = [
            map_post_to_response(
                post,
                likes_count=likes_count_map.get(post.id, 0),
                liked_by_me=post.id in liked_post_ids,
            )
            for post in posts
        ]
        
        return {"page": page, "limit": limit, "total": total, "data": posts_data}

    def get_post(self, post_id: int, current_user: User):
        post = self.repository.get_by_id(post_id, include_relations=True)
        if not post:
            raise PostNotFound()

        if post.author_id != current_user.id and current_user.role != "admin":
            raise ForbiddenAction()

        likes_count = self.like_repository.count_likes_for_post(post.id)
        liked_by_me = self.like_repository.is_post_liked_by_user(post.id, current_user.id)

        return map_post_to_response(post, likes_count, liked_by_me)

    def update_post(self, post_id: int, post_data: PostCreate, current_user: User):
        post = self.repository.get_by_id(post_id, include_relations=True)
        if not post:
            raise PostNotFound()

        if post.author_id != current_user.id:
            raise ForbiddenAction()

        updated_post = self.repository.update(post, post_data.title, post_data.content)
        
        likes_count = len(updated_post.likes)
        liked_by_me = any(like.user_id == current_user.id for like in updated_post.likes)

        return map_post_to_response(updated_post, likes_count=likes_count, liked_by_me=liked_by_me)

    def delete_post(self, post_id: int, current_user: User):
        post = self.repository.get_by_id(post_id, include_relations=False)
        if not post:
            raise PostNotFound()

        if post.author_id != current_user.id and current_user.role != "admin":
            raise ForbiddenAction()

        self.repository.delete(post)
        return {"message": "Post eliminado"}
