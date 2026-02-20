from sqlalchemy.orm import Session
from app.models.follows import Follow

class FollowerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_follow(self, follower_id: int, followed_id: int):
        return self.db.query(Follow).filter(
            Follow.follower_id == follower_id,
            Follow.followed_id == followed_id
        ).first()

    def create(self, follower_id: int, followed_id: int):
        new_follow = Follow(follower_id=follower_id, followed_id=followed_id)
        self.db.add(new_follow)
        self.db.commit()
        return new_follow

    def delete(self, follow: Follow):
        self.db.delete(follow)
        self.db.commit()

    def get_followers(self, user_id: int):
        return self.db.query(Follow).filter(Follow.followed_id == user_id).all()

    def get_following(self, user_id: int):
        return self.db.query(Follow).filter(Follow.follower_id == user_id).all()
