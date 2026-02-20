from sqlalchemy.orm import Session
from app.repositories.like_repository import LikeRepository
from app.models.post import Post
from fastapi import HTTPException

class LikeService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LikeRepository(db)

    def like_post(self, post_id: int, user_id: int):
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
            
        existing_like = self.repository.get_like(post_id, user_id)
        if existing_like:
            raise HTTPException(status_code=400, detail="You already liked this post")
            
        self.repository.create(post_id, user_id)
        likes_count = self.repository.count_by_post(post_id)
        return {"liked": True, "likes_count": likes_count}

    def unlike_post(self, post_id: int, user_id: int):
        like = self.repository.get_like(post_id, user_id)
        if not like:
            raise HTTPException(status_code=404, detail="Like not found")
            
        self.repository.delete(like)
        likes_count = self.repository.count_by_post(post_id)
        return {"liked": False, "likes_count": likes_count}
