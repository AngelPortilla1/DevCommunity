from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="unique_like"),)
