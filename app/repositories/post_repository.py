from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, func
from app.models.post import Post
from app.models.like import Like
from datetime import date, datetime, time

class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, content: str, author_id: int):
        new_post = Post(
            title=title,
            content=content,
            author_id=author_id
        )
        self.db.add(new_post)
        self.db.commit()
        self.db.refresh(new_post)
        return new_post

    def get_by_id(self, post_id: int, include_relations: bool = True):
        query = self.db.query(Post)
        if include_relations:
            query = query.options(
                selectinload(Post.author),
                selectinload(Post.likes)
            )
        return query.filter(Post.id == post_id).first()

    def get_posts(
        self,
        skip: int,
        limit: int,
        search: str | None = None,
        author_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None
    ):
        query = self.db.query(Post).options(selectinload(Post.author))

        if author_id:
            query = query.filter(Post.author_id == author_id)

        if search:
            query = query.filter(
                or_(
                    Post.title.ilike(f"%{search}%"),
                    Post.content.ilike(f"%{search}%")
                )
            )

        if from_date:
            start_datetime = datetime.combine(from_date, time.min)
            query = query.filter(Post.created_at >= start_datetime)

        if to_date:
            end_datetime = datetime.combine(to_date, time.max)
            query = query.filter(Post.created_at <= end_datetime)

        total = query.count()
        posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
        return total, posts

    def get_likes_count_for_posts(self, post_ids: list[int]):
        likes_counts = (
            self.db.query(Like.post_id, func.count(Like.id).label("count"))
            .filter(Like.post_id.in_(post_ids))
            .group_by(Like.post_id)
            .all()
        )
        return {post_id: count for post_id, count in likes_counts}

    def get_user_liked_posts(self, post_ids: list[int], user_id: int):
        user_likes = (
            self.db.query(Like.post_id)
            .filter(
                Like.post_id.in_(post_ids),
                Like.user_id == user_id
            )
            .all()
        )
        return {post_id for (post_id,) in user_likes}

    def update(self, post: Post, title: str, content: str):
        post.title = title
        post.content = content
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete(self, post: Post):
        self.db.delete(post)
        self.db.commit()
