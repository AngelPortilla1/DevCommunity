from sqlalchemy.orm import Session
from app.repositories.like_repository import LikeRepository
from app.models.post import Post
from fastapi import HTTPException
from app.services.notification_service import NotificationService

class LikeService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LikeRepository(db)
        self.notification_service = NotificationService(db)

    def like_post(self, post_id: int, user_id: int):
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
            
        existing_like = self.repository.get_like(post_id, user_id)
        if existing_like:
            raise HTTPException(status_code=400, detail="You already liked this post")
            
        self.repository.create(post_id, user_id)
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po:
            po.likes_count += 1
            self.db.commit()
            self.db.refresh(po)
            post = po

        # Notificar al autor del post
        self.notification_service.notify_like(
            post_author_id=post.author_id,
            actor_id=user_id,
            post_id=post_id,
        )

        return {"liked": True, "likes_count": post.likes_count}

    def unlike_post(self, post_id: int, user_id: int):
        like = self.repository.get_like(post_id, user_id)
        if not like:
            raise HTTPException(status_code=404, detail="Like not found")
            
        self.repository.delete(like)
        
        po = self.db.query(Post).filter(Post.id == post_id).with_for_update().first()
        if po and po.likes_count > 0:
            po.likes_count -= 1
            self.db.commit()
            self.db.refresh(po)
            post = po
        else:
            post = po if po else None
            
        return {"liked": False, "likes_count": post.likes_count if post else 0}
