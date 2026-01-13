from app.models import post
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.post import Post
from app.models.user import User
from sqlalchemy import func
from app.models.like import Like
from app.schemas import PostCreate, PostResponse, PaginatedPosts
from sqlalchemy import or_
# Importar dependencias desde auth
from app.auth.dependencies import get_current_user, admin_only
from datetime import date
from datetime import datetime, time
from app.models import  Like
from app.mappers.post_mapper import map_post_to_response
from sqlalchemy.orm import selectinload
from app.exceptions.post_exceptions import PostNotFound, ForbiddenAction
from app.repositories.like_repository import (
    count_likes_for_post,
    is_post_liked_by_user
)
from app.mappers.post_mapper import map_post_to_response

router = APIRouter(prefix="/posts", tags=["Posts"])


#Crear post 
@router.post("/", response_model=PostResponse)
def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_post = Post(
        title=post.title,
        content=post.content,
        author_id=current_user.id,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

     # Nuevo post → no tiene likes
    return map_post_to_response(
        new_post,
        likes_count=0,
        liked_by_me=False
    
    )

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
    
    query = query.options(
        selectinload(Post.author),
    )

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
    
    post_ids = [post.id for post in posts]

    ## 5️⃣  Likes count por post
    likes_counts = (
        db.query(
            Like.post_id,
            func.count(Like.id).label("count")
        )
        .filter(Like.post_id.in_(post_ids))
        .group_by(Like.post_id)
        .all()
    )

    likes_count_map = {
        post_id: count
        for post_id, count in likes_counts
    }

    # Likes del usuario actual
    user_likes = (
        db.query(Like.post_id)
        .filter(
            Like.post_id.in_(post_ids),
            Like.user_id == current_user.id
        )
        .all()
    )

    liked_post_ids = {post_id for (post_id,) in user_likes}

    # Construcción final
    posts_data = [
        map_post_to_response(
            post,
            likes_count=likes_count_map.get(post.id, 0),
            liked_by_me=post.id in liked_post_ids,
        )
        for post in posts
    ]
    return { "page": page, "limit": limit, "total": total, "data": posts_data}




#Obtener post por id
@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .options(
            selectinload(Post.author),
        )
        .filter(Post.id == post_id)
        .first()
    )

    if not post:
        raise PostNotFound()

    if post.author_id != current_user.id and current_user.role != "admin":
        raise ForbiddenAction()

    likes_count = count_likes_for_post(db, post.id)
    liked_by_me = is_post_liked_by_user(db, post.id, current_user.id)

    return map_post_to_response(
        post,
        likes_count,
        liked_by_me
    )
# ▶️ Editar post (dueño)
@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post_db = (
        db.query(Post)
        .options(
            selectinload(Post.author),
            selectinload(Post.likes),
        )
        .filter(Post.id == post_id)
        .first()
    )

    if not post_db:
        raise PostNotFound()

    if post_db.author_id != current_user.id:
        raise ForbiddenAction()

    post_db.title = post.title
    post_db.content = post.content

    db.commit()
    db.refresh(post_db)

    likes_count = len(post_db.likes)
    liked_by_me = any(
        like.user_id == current_user.id
        for like in post_db.likes
    )

    return map_post_to_response(
        post_db,
        likes_count=likes_count,
        liked_by_me=liked_by_me,
    )

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
        raise PostNotFound()

    if post_db.author_id != current_user.id and current_user.role != "admin":
        raise ForbiddenAction()

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

    likes_count = (
        db.query(Like)
        .filter(Like.post_id == post_id)
        .count()
    )

    return {
        "liked": True,
        "likes_count": likes_count
    }
    
    
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

    likes_count = (
        db.query(Like)
        .filter(Like.post_id == post_id)
        .count()
    )

    return {
        "liked": False,
        "likes_count": likes_count
    }

   
    
    
    


