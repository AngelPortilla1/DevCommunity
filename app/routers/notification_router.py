from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.notification_service import NotificationService
from app.schemas.notification_schema import (
    NotificationResponse,
    PaginatedNotifications,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(db: Session = Depends(get_db)):
    return NotificationService(db)


# Listar mis notificaciones (paginadas)
@router.get("/", response_model=PaginatedNotifications)
def get_my_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(15, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.get_my_notifications(current_user, page, size)


# Cantidad de notificaciones no leidas (badge del sidebar)
@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.get_unread_count(current_user)


# Marcar todas como leidas
@router.patch("/read-all")
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.mark_all_as_read(current_user)


# Marcar una notificacion como leida
@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    return service.mark_as_read(notification_id, current_user)
