# app/auth/auth_handler.py
import uuid
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.redis import redis_client

# Leemos la clave y algoritmo desde settings (que los toma del .env)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(data: dict) -> str:
    """Genera un token JWT firmado con la clave secreta."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Genera un refresh token JWT y lo registra en Redis."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Añadimos un identificador único (JTI) para rastrearlo
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    
    # Store in Redis: refresh_token:{jti} -> user_id
    user_id = data.get("user_id") or data.get("sub")
    redis_client.setex(
        f"refresh_token:{jti}",
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        str(user_id)
    )
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verifica y decodifica un JWT. Devuelve el payload o None si es inválido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> dict:
    """Decodifica un JWT. Lanza HTTP 401 si el token es inválido o expirado o revocado."""
    
    # 3.3 Verificación en Blacklist (Opcional - Enterprise)
    if redis_client.exists(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token revocado o sesión cerrada",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se puede usar un refresh token como access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_refresh_token(token: str) -> dict:
    """Decodifica el refresh token y verifica su validez usando Redis."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no es un refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token malformado (sin jti)",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Verify in Redis
        user_id = redis_client.get(f"refresh_token:{jti}")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revocado o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

def revoke_refresh_token(jti: str) -> None:
    """Revoca un refresh token eliminándolo de Redis."""
    redis_client.delete(f"refresh_token:{jti}")
