from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import CommentCreate, CommentResponse, CommentUpdate
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.comment_service import CommentService
from app.mappers.comment_mapper import map_comment_to_response

router = APIRouter(prefix="/comments", tags=["Comments"])

def get_comment_service(db: Session = Depends(get_db)):
    return CommentService(db)

# Crear comentario
@router.post("/{post_id}", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service)
):
    new_comment = service.create_comment(post_id, comment, current_user)
    return map_comment_to_response(new_comment)


# Obtener comentarios de un post (requiere autenticación)
@router.get("/post/{post_id}", response_model=list[CommentResponse])
def get_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service)
):
    comments = service.get_comments_by_post(post_id)
    return [map_comment_to_response(comment) for comment in comments]


# Editar comentario (solo dueño)
@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service)
):
    updated_comment = service.update_comment(comment_id, comment, current_user)
    return map_comment_to_response(updated_comment)


# Eliminar comentario (dueño o admin)
@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service)
):
    service.delete_comment(comment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
