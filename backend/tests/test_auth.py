"""
Tests unitarios de autenticacion.

Dos bloques:
  1. Utilidades puras (sin app ni DB): hashing de password y emision/validacion
     de tokens JWT.
  2. Endpoint /auth/login aislado: se monta SOLO el router de auth y se inyecta
     una base SQLite temporal con usuarios sembrados, sin levantar la app real.

La autorizacion por roles (USER vs ADMIN sobre rutas protegidas) se cubre aparte
en tests/e2e/test_e2e_roles.py.
"""
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import JWTError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import db.models  # noqa: registra los modelos con Base antes de create_all
from auth.utils import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from db.database import Base
from db.models import Role, User


# ─── 1. Utilidades puras ─────────────────────────────────────────────────────

# Verifica que el hash no sea el texto plano y que verify_password lo valide
def test_hash_password_no_guarda_texto_plano():
    hashed = hash_password("secreto123")
    assert hashed != "secreto123"
    assert verify_password("secreto123", hashed) is True


# Verifica que una password incorrecta no valide contra el hash
def test_verify_password_rechaza_incorrecta():
    hashed = hash_password("secreto123")
    assert verify_password("otra-password", hashed) is False


# Verifica el round-trip del token: lo que se codifica en "sub" se recupera al decodificar
def test_token_roundtrip_conserva_sub():
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert "exp" in payload  # create_access_token agrega expiracion


# Verifica que un token expirado sea rechazado al decodificar
def test_token_expirado_es_rechazado():
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_token(token)


# Verifica que un token manipulado (firma invalida) sea rechazado
def test_token_con_firma_invalida_es_rechazado():
    token = create_access_token({"sub": "1"})
    with pytest.raises(JWTError):
        decode_token(token + "x")


# ─── 2. Endpoint /auth/login aislado ─────────────────────────────────────────

@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/auth.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    db = Session()
    try:
        admin_role = Role(name="ADMIN")
        user_role = Role(name="USER")
        db.add_all([admin_role, user_role])
        db.commit()
        db.add(User(
            username="admin",
            hashed_password=hash_password("admin123"),
            role_id=admin_role.id,
        ))
        db.add(User(
            username="user",
            hashed_password=hash_password("user123"),
            role_id=user_role.id,
        ))
        db.commit()
    finally:
        db.close()
    return Session


@pytest.fixture
def client(session_factory):
    import auth.router as auth_router_mod

    app = FastAPI()
    app.include_router(auth_router_mod.router)

    def _get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    # Redirigir la dependencia get_db del router a la base temporal sembrada
    app.dependency_overrides[auth_router_mod.get_db] = _get_db
    return TestClient(app)


# Verifica que un login valido devuelva token, username y el rol del usuario
def test_login_exitoso_devuelve_token_y_rol(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    data = r.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["username"] == "admin"
    assert data["role"] == "ADMIN"


# Verifica que una password incorrecta devuelva 401
def test_login_password_incorrecta_devuelve_401(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "incorrecta"})
    assert r.status_code == 401


# Verifica que un usuario inexistente devuelva 401 (sin filtrar si el user existe o no)
def test_login_usuario_inexistente_devuelve_401(client):
    r = client.post("/auth/login", json={"username": "fantasma", "password": "loquesea"})
    assert r.status_code == 401


# Verifica que el token emitido por el login sea decodificable y lleve el id en "sub"
def test_login_emite_token_decodificable(client):
    r = client.post("/auth/login", json={"username": "user", "password": "user123"})
    assert r.status_code == 200
    payload = decode_token(r.json()["access_token"])
    assert payload["sub"]  # id del usuario, como string


# Verifica que el rol viaje distinto para cada usuario (USER vs ADMIN)
def test_login_devuelve_rol_correcto_por_usuario(client):
    admin = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    user = client.post("/auth/login", json={"username": "user", "password": "user123"})
    assert admin.json()["role"] == "ADMIN"
    assert user.json()["role"] == "USER"
