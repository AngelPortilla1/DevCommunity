from sqlalchemy.orm import Session
from app.repositories.follower_repository import FollowerRepository
from fastapi import HTTPException
from app.models.user import User

class FollowerService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FollowerRepository(db)

    def follow_user(self, follower_id: int, followed_id: int):
        if follower_id == followed_id:
            raise HTTPException(status_code=400, detail="You cannot follow yourself")
            
        followed_user = self.db.query(User).filter(User.id == followed_id).first()
        if not followed_user:
            raise HTTPException(status_code=404, detail="User not found")
            
        existing_follow = self.repository.get_follow(follower_id, followed_id)
        if existing_follow:
            raise HTTPException(status_code=400, detail="Already following this user")
            
        return self.repository.create(follower_id, followed_id)

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
