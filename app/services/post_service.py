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
        return map_post_to_response(new_post, liked_by_me=False)

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
        liked_post_ids = self.repository.get_user_liked_posts(post_ids, current_user.id)

        posts_data = [
            map_post_to_response(
                post,
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

        liked_by_me = self.like_repository.is_post_liked_by_user(post.id, current_user.id)

        return map_post_to_response(post, liked_by_me)

    def update_post(self, post_id: int, post_data: PostCreate, current_user: User):
        post = self.repository.get_by_id(post_id, include_relations=True)
        if not post:
            raise PostNotFound()

        if post.author_id != current_user.id:
            raise ForbiddenAction()

        updated_post = self.repository.update(post, post_data.title, post_data.content)
        
        liked_by_me = any(like.user_id == current_user.id for like in updated_post.likes)

        return map_post_to_response(updated_post, liked_by_me=liked_by_me)

    def delete_post(self, post_id: int, current_user: User):
        post = self.repository.get_by_id(post_id, include_relations=False)
        if not post:
            raise PostNotFound()

        if post.author_id != current_user.id and current_user.role != "admin":
            raise ForbiddenAction()

        self.repository.delete(post)
        return {"message": "Post eliminado"}




def get_feed(self, current_user_id: int, page: int, size: int):

    followed_ids = self.follower_repository.get_followed_ids(current_user_id)

    if not followed_ids:
        return empty_paginated_response

    posts, total = self.post_repository.get_feed_posts(
        followed_ids, page, size
    )

    post_ids = [p.id for p in posts]

    liked_ids = self.like_repository.get_liked_post_ids(
        current_user_id, post_ids
    )

    # Mapear DTO
    response_items = [
        PostResponse(
            id=p.id,
            title=p.title,
            content=p.content,
            likes_count=p.likes_count,
            comments_count=p.comments_count,
            liked_by_me=p.id in liked_ids
        )
        for p in posts
    ]

    return paginated_response
