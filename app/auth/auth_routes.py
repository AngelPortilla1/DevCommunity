from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import bcrypt
import hashlib
from app.core.database import get_db
from app.models.user import User
from app.auth.auth_handler import create_access_token
from app.schemas import UserCreate, UserLogin
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from app.auth.auth_handler import decode_access_token

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
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Verificar contraseña
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({"sub": user.email,"user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer"
    }
    
    
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
