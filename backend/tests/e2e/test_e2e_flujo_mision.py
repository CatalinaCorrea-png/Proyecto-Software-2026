"""
Tests END TO END: recorren un caso de uso completo a traves de la app real
(HTTP + WebSocket), con dron simulado, camara sintetica y detectores fake.
No requieren hardware ni MongoDB.

Cubren:
  1. Ciclo de vida de una mision: login -> setup -> arranque por WS ->
     persistencia en SQLite -> mision activa -> stop -> borrado.
  2. Flujo de deteccion: una deteccion inyectada en el detector RGB viaja por el
     WS de deteccion y termina persistida en SQLite asociada a la mision.
"""
import json

import core.detectors as detectors
import core.mission_state as ms
from core.state import drone_state
from db.database import SessionLocal
from db.models import Mission

SETUP_PAYLOAD = {
    "name": "E2E Mision",
    "lat": -33.0,
    "lng": -71.0,
    "altitude": 25.0,
    "grid_rows": 5,
    "grid_cols": 5,
    "cell_size_m": 20.0,
}


def test_flujo_mision_lifecycle(client, auth_headers):
    # Sin token, las rutas de admin no se pueden tocar
    assert client.get("/missions").status_code in (401, 403)

    # 1. Configurar la mision
    r = client.post("/mission/setup", json=SETUP_PAYLOAD, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ready"
    assert body["total_cells"] == 25  # 5 x 5

    # 2. Antes de arrancar no hay mision activa
    assert client.get("/mission/active", headers=auth_headers).json()["active"] is False

    # 3. Abrir el WS de mision: crea la mision en SQLite y arranca la simulacion
    with client.websocket_connect("/ws/mission") as ws:
        first = json.loads(ws.receive_text())
        assert first["type"] == "telemetry"
        # un segundo mensaje confirma que la simulacion esta iterando
        second = json.loads(ws.receive_text())
        assert "position" in second["data"]

    # 4. La mision quedo registrada (lista ordenada por created_at desc -> [0] es la nueva)
    missions = client.get("/missions", headers=auth_headers).json()
    assert len(missions) >= 1
    mission_id = missions[0]["id"]

    # 5. Ahora la mision figura como activa (la simulacion sigue corriendo)
    assert client.get("/mission/active", headers=auth_headers).json()["active"] is True

    # 6. Detener la mision
    r = client.post("/mission/stop", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "stopped"
    assert client.get("/mission/active", headers=auth_headers).json()["active"] is False

    # 7. Una mision detenida (no activa) se puede borrar
    assert client.delete(f"/missions/{mission_id}", headers=auth_headers).status_code == 204


def test_deteccion_se_persiste_en_sqlite(client, auth_headers):
    # 1. Configurar la mision (deja el grid armado y el dron en el centro)
    r = client.post("/mission/setup", json=SETUP_PAYLOAD, headers=auth_headers)
    assert r.status_code == 200, r.text

    # 2. Simular que hay una mision en curso: crear la fila y marcar el id activo
    db = SessionLocal()
    try:
        m = Mission(
            name="E2E Deteccion",
            status="active",
            grid_rows=5,
            grid_cols=5,
            grid_center_lat=SETUP_PAYLOAD["lat"],
            grid_center_lng=SETUP_PAYLOAD["lng"],
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        mission_id = m.id
    finally:
        db.close()
    ms.active_mission_id = mission_id
    # La inferencia ahora la corre un productor unico que vive `while mission_active`.
    # Marcamos la mision activa para que arranque al conectarse el consumidor.
    drone_state.mission_active = True

    # 3. Forzar que el detector RGB "vea" una persona, sin depender de la imagen
    detectors.yolo.next_detections = [
        {
            "bbox": {"x1": 280, "y1": 200, "x2": 360, "y2": 400, "cx": 320, "cy": 300},
            "confidence": 0.91,
            "source": "rgb",
            "timestamp": 0,
        }
    ]

    # 4. Abrir el WS de deteccion (consumidor) y leer hasta recibir una alerta "detection"
    got_detection = False
    with client.websocket_connect("/ws/detection") as ws:
        for _ in range(40):
            msg = json.loads(ws.receive_text())
            if msg["type"] == "detection":
                got_detection = True
                break
    # Frenar el productor antes de verificar la persistencia.
    drone_state.mission_active = False
    assert got_detection, "no se recibio ninguna alerta de deteccion"

    # 5. La deteccion quedo persistida en SQLite, asociada a la mision
    detail = client.get(f"/missions/{mission_id}", headers=auth_headers).json()
    assert len(detail["detections"]) >= 1
    assert detail["detections"][0]["source"] == "rgb"
    assert detail["detections"][0]["confidence"] in ("medium", "high")
