from fastapi import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import admin_only
from app.core.redis import redis_client
from app.services.session_service import SessionService

session_service = SessionService(redis_client)

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_only)
):
    return db.query(User).all()


@router.put("/users/{user_id}/role")
def update_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_only)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.role = role
    db.commit()
    db.refresh(user)

    return {"message": "Rol actualizado", "user": user}

@router.get("/users/{user_id}/sessions/metrics")
def get_user_metrics_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(admin_only)
):
    """
    5.5 - Endpoint administrativo extendido.
    Monitorea, audita y previene comportamientos maliciosos viendo en vivo 
    la calidad y telemetría de un usuario específico.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return session_service.get_metrics_for_user(user_id)
