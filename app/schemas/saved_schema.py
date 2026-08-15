from pydantic import BaseModel, ConfigDict
from app.schemas.post_schema import PostResponse


class SaveActionResponse(BaseModel):
    saved: bool
    message: str


class SavedCheckResponse(BaseModel):
    is_saved: bool
    post_id: int


class PaginatedSaved(BaseModel):
    page: int
    size: int
    total: int
    total_pages: int
    items: list[PostResponse]

    model_config = ConfigDict(from_attributes=True)
