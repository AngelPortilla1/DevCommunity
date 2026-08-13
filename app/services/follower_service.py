from sqlalchemy.orm import Session
from app.repositories.follower_repository import FollowerRepository
from fastapi import HTTPException
from app.models.user import User
from app.services.notification_service import NotificationService

class FollowerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FollowerRepository(db)
        self.notification_service = NotificationService(db)

    def follow_user(self, follower_id: int, followed_id: int):
        if follower_id == followed_id:
            raise HTTPException(status_code=400, detail="You cannot follow yourself")
            
        followed_user = self.db.query(User).filter(User.id == followed_id).first()
        if not followed_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        existing_follow = self.repository.get_follow(follower_id, followed_id)
        if existing_follow:
            raise HTTPException(status_code=400, detail="Already following this user")

        result = self.repository.create(follower_id, followed_id)

        # Notificar al usuario seguido
        self.notification_service.notify_follow(
            followed_id=followed_id,
            follower_id=follower_id,
        )

        return result

    def unfollow_user(self, follower_id: int, followed_id: int):
        follow = self.repository.get_follow(follower_id, followed_id)
        if not follow:
            raise HTTPException(status_code=404, detail="Not following this user")
            
        self.repository.delete(follow)
        return {"message": "Unfollowed successfully"}
        
    def get_followers(self, user_id: int):
        return self.repository.get_followers(user_id)
        
    def get_following(self, user_id: int):
        return self.repository.get_following(user_id)
