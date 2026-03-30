from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import bcrypt
import hashlib
from app.db.session import get_db
from app.models.user import User
from app.auth.auth_handler import (
    create_access_token, 
    decode_access_token, 
    create_refresh_token, 
    decode_refresh_token, 
    revoke_refresh_token,
    SECRET_KEY,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from app.schemas import UserCreate, UserLogin, RefreshTokenRequest
from datetime import datetime, timedelta
from jose import jwt
from app.core.redis import redis_client
from app.services.session_service import SessionService
from app.utils.device import extract_ip, extract_user_agent, generate_device_id

session_service = SessionService(redis_client)
from app.auth.auth_bearer import JWTBearer
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


router = APIRouter(prefix="/auth", tags=["Auth"])

def prepare_password(password: str) -> bytes:
    """
    Pre-hashea la contraseña con SHA256 para evitar el límite de 72 bytes de bcrypt.
    Retorna bytes para usar directamente con bcrypt.
    """
    return hashlib.sha256(password.encode('utf-8')).digest()

def hash_password(password: str) -> str:
    """Hashea la contraseña usando bcrypt con pre-hash SHA256"""
    prepared = prepare_password(password)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(prepared, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifica la contraseña contra el hash almacenado"""
    prepared = prepare_password(password)
    return bcrypt.checkpw(prepared, hashed.encode('utf-8'))

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Validar longitud mínima de contraseña
    if len(user.password) < 8:
        raise HTTPException(
            status_code=400, 
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya está registrado")

    # Hashear contraseña
    hashed_password = hash_password(user.password)
    
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role="user"  # Asignar explícitamente rol de usuario normal
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "Usuario creado exitosamente",
        "user": new_user.username
    }

@router.post("/login")
def login_user(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Verificar contraseña
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token({"sub": user.email,"user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email,"user_id": user.id})

    # Integramos session service
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = payload.get("jti")
    
    ip = extract_ip(request)
    ua = extract_user_agent(request)
    device_id = generate_device_id(request)
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    session_service.create_session(
        user_id=user.id,
        device_id=device_id,
        jti=jti,
        ip=ip,
        user_agent=ua,
        expires_at=expires_at
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
def refresh_token(request_data: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para renovar el access_token y rotar el refresh_token.
    """
    payload = decode_refresh_token(request_data.refresh_token)
    
    user_id = payload.get("user_id")
    email = payload.get("sub")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
    jti = payload.get("jti")
    # Revocar el refresh token actual por seguridad
    revoke_refresh_token(jti)
    
    new_access_token = create_access_token({"sub": email, "user_id": user_id})
    new_refresh_token = create_refresh_token({"sub": email, "user_id": user_id})
    
    new_payload = jwt.decode(new_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    new_jti = new_payload.get("jti")
    
    ip = extract_ip(request)
    ua = extract_user_agent(request)
    device_id = generate_device_id(request)
    new_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    updated = session_service.update_jti_for_session(
        user_id=user_id,
        device_id=device_id,
        old_jti=jti,
        new_jti=new_jti,
        new_expires_at=new_expires_at,
        current_ip=ip,
        current_user_agent=ua
    )
    if not updated:
        revoke_refresh_token(new_jti)
        raise HTTPException(status_code=401, detail="Sesión inválida, expirada o robada.")
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout(request_data: RefreshTokenRequest, request: Request, __token: str = Depends(oauth2_scheme)):
    """
    Cierra la sesión revocando el refresh token en Redis.
    Y añade el access_token al blacklist.
    """
    payload = decode_refresh_token(request_data.refresh_token)
    jti = payload.get("jti")
    user_id = payload.get("user_id")
    
    ip = extract_ip(request)
    device_id = generate_device_id(request)

    revoke_refresh_token(jti)
    session_service.delete_session(user_id, device_id)
    
    # 3.3 Blacklist de access_token (opcional enterprise level)
    # TTL aproximado para no acumular basura (los access tokens viven menos p.ej. 30min o 1 d).
    redis_client.setex(f"blacklist:{__token}", timedelta(minutes=60), "revoked")
    
    return {"message": "Cierre de sesión exitoso"}
    
    
@router.get("/me")
def get_me(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Token inválido o expirado")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Token malformado")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username
    }


# --- SESSION ENDPOINTS ---

@router.get("/sessions")
def get_sessions(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    sessions = session_service.get_sessions(user_id)
    return {"sessions": sessions}

@router.delete("/sessions/all")
def delete_all_other_sessions(request: Request, token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    
    ip = extract_ip(request)
    device_id = generate_device_id(request)
    
    deleted = session_service.delete_all_except(user_id, keep_device_id=device_id)
    return {"message": "Sesiones cerradas", "deleted_devices": deleted}

@router.delete("/sessions/{device_id}")
def delete_session_by_device(device_id: str, token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    user_id = payload.get("user_id")
    
    success = session_service.delete_session(user_id, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"message": "Sesión cerrada exitosamente"}
