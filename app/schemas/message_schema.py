from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.user_schema import UserPublicResponse


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime
    sender: UserPublicResponse

    model_config = ConfigDict(from_attributes=True)


class LastMessageSummary(BaseModel):
    id: int
    sender_id: int
    content: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    other_user: UserPublicResponse
    created_at: datetime
    last_message_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationListItem(BaseModel):
    id: int
    other_user: UserPublicResponse
    last_message: Optional[LastMessageSummary] = None
    unread_count: int
    created_at: datetime
    last_message_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedMessages(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int
    items: list[MessageResponse]

    model_config = ConfigDict(from_attributes=True)


class UnreadMessagesCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    marked_as_read: int
