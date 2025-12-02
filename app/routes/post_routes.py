from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas import PostCreate, PostResponse

from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import decode_access_token
from app.auth.dependencies import admin_only

router = APIRouter(prefix="/posts", tags=["Posts"])

def get_current_user(token: str, db: Session):
    """Obtiene el usuario logueado desde el token"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=403, detail="Token inválido")

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user


# ▶️ Crear post (solo autenticado)
@router.post("/", response_model=PostResponse)
def create_post(
    post: PostCreate,
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)

    new_post = Post(
        title=post.title,
        content=post.content,
        author_id=user.id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


# ▶️ Obtener todos los posts (público)
@router.get("/", response_model=list[PostResponse])
def get_posts(current_admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    # Requiere rol admin (admin_only) y luego devuelve todos los posts
    return db.query(Post).all()

#Obtener post por id (público)
@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no existe")
    return post


# ▶️ Editar post (solo dueño)
@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    post_db = db.query(Post).filter(Post.id == post_id).first()

    if not post_db:
        raise HTTPException(status_code=404, detail="Post no existe")

    if post_db.author_id != user.id:
        raise HTTPException(status_code=403, detail="No puedes editar este post")

    post_db.title = post.title
    post_db.content = post.content
    
    db.commit()
    db.refresh(post_db)

    return post_db


# ▶️ Eliminar post (dueño o admin)
@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    token: str = Depends(JWTBearer()),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    post_db = db.query(Post).filter(Post.id == post_id).first()

    if not post_db:
        raise HTTPException(status_code=404, detail="Post no existe")

    if post_db.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar este post")

    db.delete(post_db)
    db.commit()

    return {"message": "Post eliminado"}
