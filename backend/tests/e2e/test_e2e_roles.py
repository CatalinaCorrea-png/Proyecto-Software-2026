"""
Tests E2E del control de acceso por roles (feature del sprint 6).

Verifican el comportamiento de autorizacion de punta a punta sobre la app real:
un token de rol USER no puede tocar rutas de ADMIN, un token ADMIN si, y sin
token la ruta queda protegida. La validacion de credenciales del /auth/login en
si (password ok/mal, hashing, token) se cubre en tests unitarios aparte.

Los usuarios 'admin' (admin123) y 'user' (user123) los siembra seed_db().
"""


def _login(client, username: str, password: str) -> dict:
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_usuario_no_admin_recibe_403_en_ruta_admin(client):
    user_headers = _login(client, "user", "user123")
    # GET /missions es admin-only (Depends(require_admin))
    assert client.get("/missions", headers=user_headers).status_code == 403


def test_admin_si_accede_a_ruta_admin(client):
    admin_headers = _login(client, "admin", "admin123")
    r = client.get("/missions", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_sin_token_la_ruta_admin_queda_protegida(client):
    assert client.get("/missions").status_code in (401, 403)


def test_login_devuelve_rol_del_usuario(client):
    # el rol viaja en la respuesta del login (lo usa el frontend para el modo solo-lectura)
    r = client.post("/auth/login", json={"username": "user", "password": "user123"})
    assert r.status_code == 200
    assert r.json()["role"] == "USER"
