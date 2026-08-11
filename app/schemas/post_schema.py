from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.user_schema import UserResponse

class PostCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=200,
        description="Post title (3–200 characters)",
    )
    content: str = Field(
        min_length=10,
        max_length=50_000,
        description="Post content (10–50,000 characters)",
    )
    image_url: str = Field(
        min_length=5,
        description="URL de la imagen del post (obligatorio)",
    )

    @field_validator("title", "content", "image_url", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v
    
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    image_url: str
    likes_count: int
    comments_count: int
    liked_by_me: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    author: Optional["UserResponse"] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedPosts(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int
    items: list[PostResponse]

    model_config = ConfigDict(from_attributes=True)
