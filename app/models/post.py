from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
from fastapi import Query
from datetime import date


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ÚNICA relación con User
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relación SQLAlchemy
    author = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="post", cascade="all, delete")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
