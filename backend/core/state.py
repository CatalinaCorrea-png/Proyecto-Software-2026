from dataclasses import dataclass, field
import time

BASE_LAT = -32.6532
BASE_LNG = -70.0109

@dataclass
class DroneState:
    lat: float = BASE_LAT
    lng: float = BASE_LNG
    altitude: float = 25.0
    battery: float = 100.0
    status: str = "idle"
    last_update: float = field(default_factory=time.time)
    mission_start: float = field(default_factory=time.time)
    real_telemetry_active: bool = False
    last_hw_telemetry: float = 0.0
    cmd_throttle: int = 0
    cmd_pitch: int = 0
    cmd_roll: int = 0
    sim_step: int = 0
    sim_direction: int = 1
    mission_active: bool = False
    # Movimiento autónomo (máquina de estados):
    #   "idle" | "sweeping" | "awaiting_confirmation"
    #   | "revisiting" | "revisit_confirm" | "completed"
    sweep_state: str = "idle"
    sweep_paused: bool = False
    pending_detection: dict | None = None   # detección esperando al operador
    pending_since: float = 0.0              # timestamp para el auto-resume
    revisit_queue: list = field(default_factory=list)  # detecciones MEDIUM por revisar
    revisit_target: dict | None = None     # punto de la cola al que se vuela ahora
    home_lat: float = BASE_LAT             # punto de despegue (return-to-launch)
    home_lng: float = BASE_LNG
    resume_state: str = "sweeping"         # fase a retomar tras resolver un hallazgo (Opción B)

drone_state = DroneState()

from modules.mapping.grid import SearchGrid, CELL_SIZE_METERS

GRID_COLS = 20
GRID_ROWS = 22

search_grid = SearchGrid(
    center_lat=BASE_LAT,
    center_lng=BASE_LNG,
    rows=GRID_ROWS,
    cols=GRID_COLS,
)

def reset_mission(lat: float, lng: float, altitude: float,
                  rows: int, cols: int, cell_size_m: float):
    global search_grid
    drone_state.lat = lat
    drone_state.lng = lng
    drone_state.altitude = altitude
    drone_state.battery = 100.0
    drone_state.status = "idle"
    drone_state.sim_step = 0
    drone_state.sim_direction = 1
    drone_state.mission_active = False
    drone_state.cmd_throttle = 0
    drone_state.cmd_pitch = 0
    drone_state.cmd_roll = 0
    drone_state.sweep_state = "idle"
    drone_state.sweep_paused = False
    drone_state.pending_detection = None
    drone_state.pending_since = 0.0
    drone_state.revisit_queue = []
    drone_state.revisit_target = None
    drone_state.resume_state = "sweeping"
    drone_state.mission_start = time.time()

    search_grid = SearchGrid(
        center_lat=lat,
        center_lng=lng,
        rows=rows,
        cols=cols,
        cell_size_m=cell_size_m,
    )

    # El punto inicial del recorrido (sim_step=0) es la celda inferior izquierda,
    # no el centro de la grilla. Ese es el "home" para el return-to-launch y la
    # posición donde arranca el dron.
    start_lat = search_grid.origin_lat - (rows - 0.5) * search_grid.cell_lat
    start_lng = search_grid.origin_lng + 0.5 * search_grid.cell_lng
    drone_state.lat = start_lat
    drone_state.lng = start_lng
    drone_state.home_lat = start_lat
    drone_state.home_lng = start_lng
    return search_grid
