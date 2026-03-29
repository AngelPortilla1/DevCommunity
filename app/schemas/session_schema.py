from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SessionBase(BaseModel):
    session_id: str
    user_id: int
    device_id: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    expires_at: datetime


class SessionOut(SessionBase):
    is_current: bool = False


class SessionListOut(BaseModel):
    sessions: list[SessionOut]


class SessionDeleteOut(BaseModel):
    message: str
    deleted_session: Optional[str] = None