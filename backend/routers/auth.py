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


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
def register(req: RegisterRequest):
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=422, detail="Email inválido")
    if len(req.password) < 6:
        raise HTTPException(status_code=422, detail="La contraseña debe tener al menos 6 caracteres")

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == req.email.lower()).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        user = User(
            email=req.email.lower(),
            hashed_password=_hash(req.password),
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = _create_token({"sub": user.email, "role": user.role})
        return {"access_token": token, "token_type": "bearer", "email": user.email, "role": user.role}
    finally:
        db.close()


@router.post("/login")
def login(req: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == req.email.lower()).first()
        if not user or not _verify(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        token = _create_token({"sub": user.email, "role": user.role})
        return {"access_token": token, "token_type": "bearer", "email": user.email, "role": user.role}
    finally:
        db.close()
