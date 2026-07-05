"""
Fixtures para los tests END TO END del backend.

La estrategia para correr SIN hardware es cortar tres "costuras":

  1. Detectores pesados (YOLO + mediapipe): se reemplazan por fakes ANTES de
     importar la app, para no cargar el modelo .pt ni descargar nada de internet.
     El detector termico real (numpy/cv2, liviano) NO se stubea: queremos
     ejercitar la fusion real.
  2. MongoDB y listener/keepalive UDP: se mockean en el lifespan de la app.
  3. Camara real: ya queda desactivada con CAMERA_SOURCE=synthetic (ver
     tests/conftest.py); el FrameGrabber cae a frames sinteticos.

Como los frames sinteticos son grises y NO producen detecciones reales, el fake
de YOLO permite que el test inyecte detecciones deterministas
(`core.detectors.yolo.next_detections = [...]`), independizando el test de la
imagen.
"""
import sys
import types
from unittest.mock import AsyncMock

import numpy as np
import pytest
from fastapi.testclient import TestClient

# ─────────────────────────────────────────────────────────────────────────────
# 1. Stubs de detectores pesados — instalados al importar este conftest, es
#    decir, ANTES de que la app importe `core.detectors`.
# ─────────────────────────────────────────────────────────────────────────────

# --- fake YoloDetector (RGB) ---
_yolo_mod = types.ModuleType("modules.detection.yolo_detector")


class _FakeYolo:
    """Detector RGB falso. El test controla la salida via `.next_detections`."""

    def __init__(self):
        self.weights_name = "fake-e2e.pt"
        self.weights_rel = "fake-e2e.pt"
        self.imgsz = 640
        self.person_class_id = 0
        self.next_detections: list[dict] = []

    def detect(self, frame):
        # copia defensiva: no compartimos la lista mutable con el caller
        return [dict(d) for d in self.next_detections]

    def draw(self, frame, detections):
        return frame


_yolo_mod.YoloDetector = _FakeYolo
_yolo_mod.CONFIDENCE_THRESHOLD = 0.5
sys.modules["modules.detection.yolo_detector"] = _yolo_mod


# --- fake ThermalSimulator ---
_ts_mod = types.ModuleType("modules.detection.thermal_simulator")


class _FakeThermalSim:
    def __init__(self, frame_w: int = 640, frame_h: int = 480):
        self.frame_w = frame_w
        self.frame_h = frame_h

    def generate(self, frame_bgr):
        # matriz a temperatura ambiente -> el detector termico real no marca nada,
        # asi la fusion depende solo de lo que inyecte el fake de YOLO.
        return np.full((24, 32), 20.0, dtype=float)

    def overlay_on_frame(self, rgb_frame, temp_matrix, alpha: float = 0.45):
        return rgb_frame

    def to_visual_frame(self, temp_matrix, target_w, target_h):
        return np.zeros((target_h, target_w, 3), dtype=np.uint8)


_ts_mod.ThermalSimulator = _FakeThermalSim
sys.modules["modules.detection.thermal_simulator"] = _ts_mod


# ─────────────────────────────────────────────────────────────────────────────
# 2. App real con infra/red neutralizada
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def app():
    import main  # dispara init_db()/seed_db() sobre el SQLite temporal

    # Neutralizar lo que el lifespan toca de infra/hardware:
    main.mongo_connect = AsyncMock()          # sin MongoDB
    main.mongo_disconnect = AsyncMock()
    main.hw_watchdog = AsyncMock()            # sin watchdog de hardware
    main.start_udp_listener = AsyncMock(
        return_value=types.SimpleNamespace(close=lambda: None)
    )
    main.drone.keepalive_loop = AsyncMock()   # sin keepalive UDP al dron
    return main.app


@pytest.fixture
def client(app):
    # El context manager dispara el lifespan (startup/shutdown) ya con los mocks.
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Token real: login contra /auth con el admin que siembra seed_db()."""
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(autouse=True)
def _reset_state():
    """Limpia los singletons de modulo entre tests (estado global del backend)."""
    import core.detectors as detectors
    import core.mission_state as ms
    import core.state as state

    def _clean():
        state.drone_state.mission_active = False
        ms.grid_clients.clear()
        ms.detection_clients.clear()
        ms.detection_history.clear()
        ms.active_mission_id = None
        ms.simulation_task = None
        ms.detection_task = None
        ms.mission_configured = False
        ms.mission_name = ""
        ms.mission_altitude = None
        ms.mission_cell_size_m = None
        detectors.yolo.next_detections = []

    _clean()
    yield
    _clean()
