from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.coments import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas import CommentCreate, CommentResponse

from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import decode_access_token
from app.auth.dependencies import admin_only

router = APIRouter(prefix="/comments", tags=["Comments"])

# Obtener usuario desde token
def get_current_user(token: str, db: Session):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Token inválido")
    
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# Crear comentario
@router.post("/{post_id}", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)

    # Validar post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no existe")

    new_comment = Comment(
        content=comment.content,
        author_id=user.id,
        post_id=post_id
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


# Obtener comentarios de un post
@router.get("/post/{post_id}", response_model=list[CommentResponse])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.post_id == post_id).all()


# Editar comentario (solo dueño)
@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment: CommentCreate,
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    comment_db = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment_db:
        raise HTTPException(status_code=404, detail="Comentario no existe")

    if comment_db.author_id != user.id:
        raise HTTPException(status_code=403, detail="No puedes editar este comentario")

    comment_db.content = comment.content
    db.commit()
    db.refresh(comment_db)

    return comment_db


# Eliminar comentario (dueño o admin)
@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    comment_db = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment_db:
        raise HTTPException(status_code=404, detail="Comentario no existe")

    if comment_db.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="No puedes borrar este comentario")

    db.delete(comment_db)
    db.commit()
    return {"message": "Comentario eliminado"}
