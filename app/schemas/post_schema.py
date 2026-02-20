from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.user_schema import UserResponse

class PostCreate(BaseModel):
    title: str
    content: str
    
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    likes_count: int
    liked_by_me: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    
    author: Optional["UserResponse"] = None 
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedPosts(BaseModel):
    page: int
    limit: int
    total: int
    data: list[PostResponse]

    model_config = ConfigDict(from_attributes=True)
