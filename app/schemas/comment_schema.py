from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.user_schema import UserPublicResponse

class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    author: UserPublicResponse
    post_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
        
class CommentUpdate(BaseModel):
    content: str
