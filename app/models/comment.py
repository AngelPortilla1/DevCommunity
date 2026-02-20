# app/models/comment.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
