from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SessionOut(BaseModel):
    device_id: str
    os: Optional[str] = None
    browser: Optional[str] = None
    ip: Optional[str] = None
    is_current: bool
    created_at: datetime
    last_access: Optional[datetime] = None
    refresh_count: int
    device_type: Optional[str] = None
    trust_level: Optional[str] = None

    @classmethod
    def from_redis_hash(cls, session_hash: dict, current_device_id: str) -> "SessionOut":
        """
        Convierte el hash subyacente de Redis en el objeto SessionOut estandarizado
        enviado al frontend.
        """
        last_access_raw = session_hash.get("last_access")
        last_access_dt = datetime.fromisoformat(last_access_raw) if last_access_raw else None
        
        created_at_raw = session_hash.get("created_at")
        created_at_dt = datetime.fromisoformat(created_at_raw) if created_at_raw else datetime.utcnow()

        return cls(
            device_id=session_hash.get("device_id", ""),
            os=session_hash.get("os", "Unknown OS"),
            browser=session_hash.get("browser", "Unknown Browser"),
            ip=session_hash.get("last_ip"),
            is_current=(session_hash.get("device_id") == current_device_id),
            created_at=created_at_dt,
            last_access=last_access_dt,
            refresh_count=session_hash.get("refresh_count", 0),
            device_type=session_hash.get("device_type", "unknown"),
            trust_level=session_hash.get("trust_level", "low")
        )
