from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas import PostCreate, PostResponse, PaginatedPosts
from app.auth.dependencies import get_current_user, admin_only
from datetime import date
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])

def get_post_service(db: Session = Depends(get_db)):
    return PostService(db)

# Crear post 
@router.post("/", response_model=PostResponse)
def create_post(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    return service.create_post(post, current_user)

# Obtener posts (con paginación + búsqueda)
@router.get("/", response_model=PaginatedPosts)
def get_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    author_id: int | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    return service.get_posts(
        page=page,
        limit=limit,
        search=search,
        author_id=author_id,
        from_date=from_date,
        to_date=to_date,
        current_user=current_user
    )

# Obtener post por id
@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    return service.get_post(post_id, current_user)

# Editar post (dueño)
@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    return service.update_post(post_id, post, current_user)

# Eliminar post (dueño o admin)
@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service)
):
    return service.delete_post(post_id, current_user)

# ADMIN: Corregir roles de usuarios (DEBUG)
@router.post("/admin/fix-roles")
def fix_user_roles(current_user: User = Depends(admin_only), db: Session = Depends(get_db)):
    db.query(User).filter(User.role == None).update({User.role: "user"})
    db.commit()
    all_users = db.query(User).all()
    return {
        "message": "Roles corregidos",
        "users": [{"id": u.id, "email": u.email, "role": u.role} for u in all_users]
    }
