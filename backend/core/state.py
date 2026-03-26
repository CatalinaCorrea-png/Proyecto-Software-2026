# Estado global en memoria del servidor
# Cuando el WS de telemetría recibe posición GPS, la guarda acá
# Cuando el WS de detección hace una detección, lee la posición de acá

from dataclasses import dataclass, field
import time

@dataclass
class DroneState:
    lat: float = -34.6083
    lng: float = -58.3712
    altitude: float = 25.0
    battery: float = 100.0
    status: str = "idle"
    last_update: float = field(default_factory=time.time)

drone_state = DroneState()

# Grilla — se inicializa cuando arranca la misión
from modules.mapping.grid import SearchGrid
search_grid = SearchGrid(
    center_lat=-34.6083,
    center_lng=-58.3712,
    rows=15,
    cols=20
)