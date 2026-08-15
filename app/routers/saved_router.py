from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.saved_service import SavedService
from app.schemas.saved_schema import (
    SaveActionResponse,
    SavedCheckResponse,
    PaginatedSaved,
)

router = APIRouter(prefix="/saved", tags=["Saved Posts"])


def get_saved_service(db: Session = Depends(get_db)):
    return SavedService(db)


# Guardar un post
@router.post("/{post_id}", status_code=status.HTTP_201_CREATED, response_model=SaveActionResponse)
def save_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: SavedService = Depends(get_saved_service),
):
    return service.save_post(post_id, current_user)


# Quitar de guardados
@router.delete("/{post_id}", status_code=status.HTTP_200_OK, response_model=SaveActionResponse)
def unsave_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: SavedService = Depends(get_saved_service),
):
    return service.unsave_post(post_id, current_user)


# Mis posts guardados (paginados)
@router.get("/", response_model=PaginatedSaved)
def get_saved_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: SavedService = Depends(get_saved_service),
):
    return service.get_saved_posts(current_user, page=page, size=size)


# Verificar si un post esta guardado por el usuario actual
@router.get("/{post_id}/check", response_model=SavedCheckResponse)
def check_post_saved(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: SavedService = Depends(get_saved_service),
):
    return service.check_saved(post_id, current_user)
