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
    drone_state.mission_start = time.time()

    search_grid = SearchGrid(
        center_lat=lat,
        center_lng=lng,
        rows=rows,
        cols=cols,
        cell_size_m=cell_size_m,
    )
    return search_grid
