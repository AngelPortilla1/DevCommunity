from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas import PostCreate, PostResponse

# Importar dependencias desde auth
from app.auth.dependencies import get_current_user, admin_only

router = APIRouter(prefix="/posts", tags=["Posts"])

# ▶️ Crear post (solo autenticado)
@router.post("/", response_model=PostResponse)
def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo post. Requiere autenticación."""
    new_post = Post(
        title=post.title,
        content=post.content,
        author_id=current_user.id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


# ▶️ Obtener todos los posts
@router.get("/", response_model=list[PostResponse])
def get_posts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtener posts. Usuarios ven solo los suyos, admins ven todos."""
    print(f"DEBUG: user_id={current_user.id}, email={current_user.email}, role={current_user.role!r}")
    if current_user.role == "admin":
        return db.query(Post).all()
    # Usuario normal: solo sus posts
    return db.query(Post).filter(Post.author_id == current_user.id).all()


# ▶️ Obtener post por id
@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtener un post específico. Usuarios solo ven los suyos, admins ven cualquiera."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no existe")
    
    # Admin ve cualquier post, usuario solo el suyo
    if current_user.role != "admin" and post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes ver este post")
    
    return post



# ▶️ Editar post (solo dueño, admin NO PUEDE editar)
@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Editar un post. Solo el propietario puede hacerlo. Admin NO puede editar."""
    post_db = db.query(Post).filter(Post.id == post_id).first()

    if not post_db:
        raise HTTPException(status_code=404, detail="Post no existe")

    # Solo el dueño puede editar (admin NO puede)
    if post_db.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el propietario del post puede editarlo")

    post_db.title = post.title
    post_db.content = post.content
    
    db.commit()
    db.refresh(post_db)

    return post_db



# ▶️ Eliminar post (dueño o admin)
@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un post. Solo el propietario o admin pueden hacerlo."""
    post_db = db.query(Post).filter(Post.id == post_id).first()

    if not post_db:
        raise HTTPException(status_code=404, detail="Post no existe")

    if post_db.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para borrar este post")

    db.delete(post_db)
    db.commit()

    return {"message": "Post eliminado"}


# ▶️ ADMIN: Corregir roles de usuarios (DEBUG)
@router.post("/admin/fix-roles")
def fix_user_roles(current_user: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Corregir roles NULL de usuarios (asignar 'user' a los que no tienen rol)."""
    # Actualizar todos los usuarios con role NULL a 'user'
    db.query(User).filter(User.role == None).update({User.role: "user"})
    db.commit()
    
    # Devolver estado
    all_users = db.query(User).all()
    return {
        "message": "Roles corregidos",
        "users": [{"id": u.id, "email": u.email, "role": u.role} for u in all_users]
    }
