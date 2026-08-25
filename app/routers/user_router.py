from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.user_schema import UserPublicResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/search", response_model=list[UserPublicResponse])
def search_users(
    q: str = Query(..., min_length=1, max_length=100, description="Término de búsqueda por username"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Busca usuarios por username (coincidencia parcial, case-insensitive).
    Excluye al usuario autenticado de los resultados.
    """
    results = (
        db.query(User)
        .filter(
            User.username.ilike(f"%{q}%"),
            User.id != current_user.id,
        )
        .limit(limit)
        .all()
    )
    return results
