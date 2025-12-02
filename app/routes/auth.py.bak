from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import decode_access_token

@router.get("/me", dependencies=[Depends(JWTBearer())])
def get_current_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "username": user.username,
        "email": user.email
    }
