from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user_schema import UserPublicResponse


class NotificationResponse(BaseModel):
    id:           int
    type:         str
    is_read:      bool
    created_at:   datetime
    post_id:      Optional[int] = None
    post_title:   Optional[str] = None
    actor:        UserPublicResponse

    model_config = ConfigDict(from_attributes=True)


class PaginatedNotifications(BaseModel):
    page:        int
    size:        int
    total:       int
    total_pages: int
    items:       list[NotificationResponse]

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int
