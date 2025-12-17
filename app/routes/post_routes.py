from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas import PostCreate, PostResponse, PaginatedPosts
from sqlalchemy import or_
# Importar dependencias desde auth
from app.auth.dependencies import get_current_user, admin_only
from datetime import date
from datetime import datetime, time
from app.models import  Like


router = APIRouter(prefix="/posts", tags=["Posts"])

#  Crear post (solo autenticado)
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

#  Obtener posts (con paginación + búsqueda)

@router.get("/", response_model=PaginatedPosts)
def get_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    author_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1️⃣ Base query según rol
    if current_user.role == "admin":
        query = db.query(Post)
        if author_id:
            query = query.filter(Post.author_id == author_id)
    else:
        query = db.query(Post).filter(Post.author_id == current_user.id)

    # 2️⃣ Búsqueda
    if search:
        query = query.filter(
            Post.title.ilike(f"%{search}%") |
            Post.content.ilike(f"%{search}%")
        )

    # 3️⃣ Filtros por fecha
    if from_date:
        start_datetime = datetime.combine(from_date, time.min)
        query = query.filter(Post.created_at >= start_datetime)

    if to_date:
        end_datetime = datetime.combine(to_date, time.max)
        query = query.filter(Post.created_at <= end_datetime)

    # 4️⃣ Paginación
    total = query.count()
    skip = (page - 1) * limit

    posts = (
        query.order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    # 5️⃣ CONSTRUCCIÓN DE DATA CON LIKES 👈 AQUÍ VA
    posts_data = []

    for post in posts:
        likes_count = len(post.likes)
        liked_by_me = any(
            like.user_id == current_user.id
            for like in post.likes
        )

        posts_data.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "author": post.author,
            "likes_count": likes_count,
            "liked_by_me": liked_by_me,
        })

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": posts_data
    }





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
  
  
  
    
 #RUTAS DE LIKES   
 
@router.post("/{post_id}/like", status_code=status.HTTP_201_CREATED)
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()

    if existing_like:
        raise HTTPException(
            status_code=400,
            detail="You already liked this post"
        )

    like = Like(
        user_id=current_user.id,
        post_id=post_id
    )
    db.add(like)
    db.commit()

    return {"message": "Post liked"}
    
    
#BORRAR UN LIKE DE UN POST 
@router.delete("/{post_id}/like", status_code=status.HTTP_200_OK)
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    like = db.query(Like).filter(
        Like.post_id == post_id,
        Like.user_id == current_user.id
    ).first()

    if not like:
        raise HTTPException(
            status_code=404,
            detail="Like not found"
        )

    db.delete(like)
    db.commit()

    return {"message": "Like removed"}

   
    
    
    


