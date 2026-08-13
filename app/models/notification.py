from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import enum


class NotificationType(str, enum.Enum):
    like    = "like"
    comment = "comment"
    follow  = "follow"


class Notification(Base):
    __tablename__ = "notifications"

    id            = Column(Integer, primary_key=True, index=True)
    recipient_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type          = Column(SAEnum(NotificationType), nullable=False)
    post_id       = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    is_read       = Column(Boolean, default=False, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relaciones de navegacion (solo lectura)
    recipient = relationship("User", foreign_keys=[recipient_id])
    actor     = relationship("User", foreign_keys=[actor_id])
    post      = relationship("Post", foreign_keys=[post_id])
