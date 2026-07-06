from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import User
from auth.utils import decode_token

bearer_scheme = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise exc
    return user


# Jerarquía de roles: cada rol incluye los permisos de los inferiores.
# El operador (ADMIN) también es espectador (GUEST/USER), por eso comparamos
# por rango y no por igualdad exacta.
ROLE_RANK = {"GUEST": 0, "USER": 1, "ADMIN": 2}


def require_role(minimo: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_RANK.get(current_user.role.name, -1) < ROLE_RANK[minimo]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol {minimo} o superior",
            )
        return current_user

    return checker


# Alias retrocompatible: las rutas de control siguen usando require_admin.
require_admin = require_role("ADMIN")
