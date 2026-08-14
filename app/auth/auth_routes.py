from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import bcrypt
import hashlib
import json
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
from app.models.session import SessionOut
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.redis import redis_client
from app.services.session_service import SessionService
from app.utils.device import extract_ip, extract_user_agent, generate_device_id

session_service = SessionService(redis_client)

# Reutilizamos el oauth2_scheme centralizado de core/dependencies.
# Un unico candado en Swagger, esquema OAuth2PasswordBearer consistente en toda la API.
from app.core.dependencies import oauth2_scheme, get_current_user


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
    
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email ya está registrado")
        
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Nombre de usuario ya está registrado")

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


def _authenticate_and_create_tokens(email: str, password: str, request: Request, db: Session) -> dict:
    """
    Lógica interna compartida entre /auth/login (JSON) y /auth/token (form-data).
    Valida credenciales, genera tokens, crea sesión en Redis.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Verificar contraseña
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token({"sub": user.email,"user_id": user.id})
    refresh_token = create_refresh_token({"sub": user.email,"user_id": user.id})

    # Integramos session service
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = payload.get("jti")
    
    ip = extract_ip(request)
    ua = extract_user_agent(request)
    device_id = generate_device_id(request)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
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


@router.post("/login")
def login_user(
    request: Request, 
    login_data: UserLogin, 
    db: Session = Depends(get_db)
):
    """Login con JSON body — usado por el frontend."""
    return _authenticate_and_create_tokens(
        email=login_data.email,
        password=login_data.password,
        request=request,
        db=db
    )


@router.post("/token")
def login_for_swagger(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint compatible con OAuth2/Swagger para obtener token via form-data.
    El campo 'username' de OAuth2PasswordRequestForm recibe el email del usuario.
    """
    return _authenticate_and_create_tokens(
        email=form_data.username,
        password=form_data.password,
        request=request,
        db=db
    )


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
    new_expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
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
def logout(
    request_data: RefreshTokenRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    """
    Cierra la sesión revocando el refresh token en Redis.
    Y añade el access_token al blacklist.
    """
    payload = decode_refresh_token(request_data.refresh_token)
    jti = payload.get("jti")

    device_id = generate_device_id(request)

    revoke_refresh_token(jti)
    session_service.delete_session(current_user.id, device_id)
    
    # 3.3 Blacklist de access_token (opcional enterprise level)
    # TTL aproximado para no acumular basura (los access tokens viven menos p.ej. 30min o 1 d).
    redis_client.setex(f"blacklist:{token}", timedelta(minutes=60), "revoked")
    
    return {"message": "Cierre de sesión exitoso"}
    
    
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username
    }


# --- SESSION ENDPOINTS ---

@router.get("/sessions")
def get_sessions(request: Request, current_user: User = Depends(get_current_user)):
    current_device_id = generate_device_id(request)
    
    sessions = session_service.get_sessions(current_user.id)
    session_outs = [SessionOut.from_redis_hash(s, current_device_id) for s in sessions]
    return {"sessions": session_outs}

@router.get("/sessions/me", response_model=SessionOut)
def get_current_session(request: Request, current_user: User = Depends(get_current_user)):
    device_id = generate_device_id(request)
    
    key = session_service._session_key(current_user.id, device_id)
    raw = session_service.redis.get(key)
    
    if not raw:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o ha expirado")
        
    session_data = json.loads(raw)
    return SessionOut.from_redis_hash(session_data, current_device_id=device_id)

@router.delete("/sessions/terminate-others")
def delete_all_other_sessions(request: Request, current_user: User = Depends(get_current_user)):
    device_id = generate_device_id(request)
    
    deleted = session_service.delete_all_except(current_user.id, keep_device_id=device_id)
    return {"message": "Sesiones de otros dispositivos cerradas", "deleted_devices": deleted}

@router.delete("/sessions/{device_id}")
def delete_session_by_device(device_id: str, current_user: User = Depends(get_current_user)):
    success = session_service.delete_session(current_user.id, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"message": "Sesión cerrada exitosamente"}

@router.get("/sessions/metrics")
def get_session_metrics(current_user: User = Depends(get_current_user)):
    """
    Endpoint de auditoria. Devuelve métricas calculadas sobre todas las sesiones.
    """
    metrics = session_service.get_metrics_for_user(current_user.id)
    return metrics
