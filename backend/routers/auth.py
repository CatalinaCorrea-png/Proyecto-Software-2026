from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
import bcrypt
from datetime import datetime, timedelta, timezone
from db.database import SessionLocal
from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "aerosearch-secret-key-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

ADMIN_EMAIL = "admin@aerosearch.ai"
ADMIN_PASSWORD = "aerosearch2026"

_security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub", "")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    finally:
        db.close()


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _get_or_create_admin(db) -> User:
    user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if not user:
        user = User(
            email=ADMIN_EMAIL,
            hashed_password=_hash(ADMIN_PASSWORD),
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    if req.email.lower() != ADMIN_EMAIL or req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    db = SessionLocal()
    try:
        user = _get_or_create_admin(db)
        token = _create_token({"sub": user.email, "role": user.role})
        return {"access_token": token, "token_type": "bearer", "email": user.email, "role": user.role}
    finally:
        db.close()
