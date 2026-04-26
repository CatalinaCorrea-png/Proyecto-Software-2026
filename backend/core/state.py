from dataclasses import dataclass, field
import time

#-- Aconcagua
BASE_LAT = -32.6532
BASE_LNG = -70.0109

#-- Plaza de Mayo
# BASE_LAT = -34.6083
# BASE_LNG = -58.3712

@dataclass
class DroneState:
    lat: float = BASE_LAT
    lng: float = BASE_LNG
    altitude: float = 25.0 # -> altitude set
    battery: float = 100.0
    status: str = "idle"
    last_update: float = field(default_factory=time.time)
    mission_start: float = field(default_factory=time.time)  # ← para tomar tiempo de la mision

drone_state = DroneState()

from modules.mapping.grid import SearchGrid, CELL_LAT, CELL_LNG

GRID_COLS = 20
GRID_ROWS = 22

# Centrar la grilla donde arranca el simulador
# El simulador hace 20 filas x 20 cols desde BASE_LAT/LNG hacia abajo-derecha
# Entonces centramos la grilla en el punto medio del recorrido
search_grid = SearchGrid(
    center_lat=BASE_LAT + (GRID_ROWS / 2) * CELL_LAT,   # centro de las rows
    center_lng=BASE_LNG + (GRID_COLS / 2) * CELL_LNG,   # centro de las cols
    rows=GRID_ROWS,
    cols=GRID_COLS
)