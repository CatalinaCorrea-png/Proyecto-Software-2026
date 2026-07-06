import pytest
from unittest.mock import AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import db.models  # noqa: registra los modelos con Base antes de create_all
from db.database import Base
from db.models import Mission


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


@pytest.fixture
def client(session_factory, monkeypatch):
    import routers.missions_sql as sql_router
    from auth.dependencies import get_current_user, require_admin

    # Redirigir SessionLocal al SQLite temporal en lugar de aerosearch.db
    monkeypatch.setattr(sql_router, "SessionLocal", session_factory)
    # delete_images_by_mission llama a MongoDB; lo reemplazamos con un mock async
    monkeypatch.setattr(sql_router, "delete_images_by_mission", AsyncMock())

    app = FastAPI()
    app.include_router(sql_router.router)
    # Las rutas estan detras de auth (require_admin / get_current_user). Estos son
    # tests de integracion del router de misiones: NO probamos la autenticacion aca,
    # asi que la anulamos con dependency_overrides para enfocarnos en la logica.
    # La auth (login y roles) se cubre aparte: login -> tests unitarios;
    # roles -> tests E2E en tests/e2e/test_e2e_roles.py.
    app.dependency_overrides[require_admin] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: None
    return TestClient(app)


# ─── GET /mission/active ─────────────────────────────────────────────────────

# Verifica que el endpoint retorne active=false cuando no hay misión
# configurada ni activa (estado inicial del sistema)
def test_mission_active_false_by_default(client, monkeypatch):
    import core.mission_state as ms
    monkeypatch.setattr(ms, "mission_configured", False)

    response = client.get("/mission/active")
    assert response.status_code == 200
    assert response.json()["active"] == False


# ─── GET /missions ────────────────────────────────────────────────────────────

# Verifica que la lista de misiones esté vacía en una base de datos nueva,
# sin registros previos
def test_list_missions_empty_on_fresh_db(client):
    response = client.get("/missions")
    assert response.status_code == 200
    assert response.json() == []


# Verifica que la lista incluya las misiones que ya existen en la base de datos
def test_list_missions_returns_existing_missions(client, session_factory):
    db = session_factory()
    db.add(Mission(
        name="Misión A", status="completed",
        grid_rows=5, grid_cols=5,
        grid_center_lat=-33.0, grid_center_lng=-71.0,
    ))
    db.commit()
    db.close()

    response = client.get("/missions")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Misión A"


# ─── POST /mission/setup ─────────────────────────────────────────────────────

# Verifica que configurar una misión retorne status "ready" y que
# total_cells sea exactamente rows × cols
def test_mission_setup_returns_ready_with_correct_cells(client):
    response = client.post("/mission/setup", json={
        "name": "Misión Test",
        "lat": -33.0,
        "lng": -71.0,
        "altitude": 25.0,
        "grid_rows": 5,
        "grid_cols": 5,
        "cell_size_m": 20.0,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["name"] == "Misión Test"
    assert data["total_cells"] == 25


# Verifica que el campo total_cells refleje correctamente grids de distintas
# dimensiones (asimetría filas ≠ columnas)
def test_mission_setup_total_cells_matches_asymmetric_grid(client):
    response = client.post("/mission/setup", json={
        "lat": -33.0,
        "lng": -71.0,
        "grid_rows": 4,
        "grid_cols": 6,
    })
    assert response.status_code == 200
    assert response.json()["total_cells"] == 24


# ─── DELETE /missions/{id} ───────────────────────────────────────────────────

# Verifica que intentar borrar una misión inexistente retorne 404
def test_delete_nonexistent_mission_returns_404(client):
    response = client.delete("/missions/9999")
    assert response.status_code == 404


# Verifica que no se pueda borrar una misión activa (el drone está en vuelo),
# devolviendo 409 Conflict
def test_delete_active_mission_returns_409(client, session_factory):
    db = session_factory()
    m = Mission(
        name="En vuelo", status="active",
        grid_rows=5, grid_cols=5,
        grid_center_lat=-33.0, grid_center_lng=-71.0,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    mission_id = m.id
    db.close()

    response = client.delete(f"/missions/{mission_id}")
    assert response.status_code == 409


# Verifica que borrar una misión completada sea exitoso (204 No Content)
def test_delete_completed_mission_returns_204(client, session_factory):
    db = session_factory()
    m = Mission(
        name="Completada", status="completed",
        grid_rows=5, grid_cols=5,
        grid_center_lat=-33.0, grid_center_lng=-71.0,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    mission_id = m.id
    db.close()

    response = client.delete(f"/missions/{mission_id}")
    assert response.status_code == 204
