from dataclasses import dataclass, field
import time

BASE_LAT = -34.6083
BASE_LNG = -58.3712

@dataclass
class DroneState:
    lat: float = BASE_LAT
    lng: float = BASE_LNG
    altitude: float = 25.0
    battery: float = 100.0
    status: str = "idle"
    last_update: float = field(default_factory=time.time)
    mission_start: float = field(default_factory=time.time)  # ← nuevo

drone_state = DroneState()

from modules.mapping.grid import SearchGrid

# Centrar la grilla donde arranca el simulador
# El simulador hace 20 filas x 20 cols desde BASE_LAT/LNG hacia abajo-derecha
# Entonces centramos la grilla en el punto medio del recorrido
search_grid = SearchGrid(
    center_lat=BASE_LAT + (10 * 0.0002),   # mitad de 20 filas
    center_lng=BASE_LNG + (10 * 0.0003),   # mitad de 20 cols
    rows=22,
    cols=22
)