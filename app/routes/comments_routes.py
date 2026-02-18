from fastapi import APIRouter, Depends, status, Response, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.coments import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas import CommentCreate, CommentResponse, CommentUpdate
from app.auth.dependencies import get_current_user
from app.exceptions.comment_exceptions import (
    CommentNotFound,
    ForbiddenCommentAction
)
from app.exceptions.post_exceptions import PostNotFound
from app.mappers.comment_mapper import map_comment_to_response


router = APIRouter(prefix="/comments", tags=["Comments"])


# Crear comentario
@router.post("/{post_id}", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise PostNotFound()

    new_comment = Comment(
        content=comment.content,
        author_id=current_user.id,
        post_id=post_id
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return map_comment_to_response(new_comment)


# Obtener comentarios de un post (requiere autenticación)
@router.get("/post/{post_id}", response_model=list[CommentResponse])
def get_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el post existe
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise PostNotFound()

    comments = db.query(Comment).filter(Comment.post_id == post_id).all()

    return [
        map_comment_to_response(comment)
        for comment in comments
    ]

# Editar comentario (solo dueño)
@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment_db = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment_db:
        raise CommentNotFound()

    if comment_db.author_id != current_user.id:
        raise ForbiddenCommentAction()

    comment_db.content = comment.content
    db.commit()
    db.refresh(comment_db)

    return map_comment_to_response(comment_db)


# Eliminar comentario (dueño o admin)
@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment_db = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment_db:
        raise CommentNotFound()

    if (
        comment_db.author_id != current_user.id
        and current_user.role != "admin"
    ):
        raise ForbiddenCommentAction()

    db.delete(comment_db)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
