from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.auth.auth_handler import decode_access_token

# FastAPI usará este esquema para leer el token del header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia que extrae y valida el JWT del header Authorization.
    - Verifica firma, expiración Y el blacklist de Redis (tokens revocados por logout).
    - 401 si el token falta, es inválido, expiró o fue revocado.
    - 404 si el usuario del token ya no existe en la BD.
    """
    # decode_access_token ya verifica: firma, expiración, tipo y blacklist de Redis.
    # Lanza HTTP 401 automáticamente si cualquiera de esas validaciones falla.
    payload = decode_access_token(token)

    email: str | None = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado: token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return user


def admin_only(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependencia que exige que el usuario autenticado tenga rol 'admin'.
    - 403 si el usuario no es admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requieren permisos de administrador"
        )
    return current_user
