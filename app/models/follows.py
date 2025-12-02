from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.core.database import Base

class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    followed_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (UniqueConstraint("follower_id", "followed_id", name="unique_follow"),)
