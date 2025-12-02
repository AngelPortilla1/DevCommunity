from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

from fastapi import HTTPException
# Clave secreta (puedes moverla a .env después)
SECRET_KEY = "mi_super_clave_ultra_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    """Genera un token JWT a partir de un diccionario"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verifica y decodifica un JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Payload decodificado:", payload)
        return payload
    except JWTError as e:
        print("Error decodificando token:", str(e))
        raise HTTPException(status_code=403, detail="Token inválido o expirado")
