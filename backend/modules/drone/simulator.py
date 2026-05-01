import asyncio
import math
import time
from core.state import drone_state, BASE_LAT, BASE_LNG, search_grid
from modules.mapping.grid import CELL_LAT, CELL_LNG, CELL_SIZE_METERS

DRONE_SPEED_MPS = 5.0
MAX_MANUAL_SPEED_MPS = 10.0
SECONDS_PER_CELL = int(CELL_SIZE_METERS / DRONE_SPEED_MPS)

async def simulate_telemetry():
    step = 0
    battery = 100.0
    spc = SECONDS_PER_CELL
    cols = search_grid.cols

    # Barrido horizontal: de centro-de-col-0 a centro-de-col-(cols-1) => (cols-1) celdas
    # Tramo vertical: 1 celda hacia arriba (al centro de la fila siguiente)
    steps_horizontal = (cols - 1) * spc
    steps_vertical = spc
    steps_per_cycle = steps_horizontal + steps_vertical

    while True:
        elapsed = int(time.time() - drone_state.mission_start)

        if battery <= 0:
            yield {
                "type": "telemetry",
                "data": {
                    "position": {
                        "lat": drone_state.lat,
                        "lng": drone_state.lng,
                        "altitude": 0.0,
                        "timestamp": int(time.time() * 1000)
                    },
                    "battery": 0.0,
                    "status": "landed",
                    "speed": 0.0,
                    "elapsed": elapsed
                }
            }
            return

        if drone_state.real_telemetry_active:
            source = "hardware"
            current_speed = DRONE_SPEED_MPS

        elif drone_state.cmd_throttle > 0:
            source = "manual"
            thrust = drone_state.cmd_throttle / 255.0
            pitch_norm = drone_state.cmd_pitch / 100.0
            roll_norm = drone_state.cmd_roll / 100.0

            speed_mps = thrust * MAX_MANUAL_SPEED_MPS
            drone_state.lat += (speed_mps * pitch_norm) / 111_000
            cos_lat = max(math.cos(math.radians(drone_state.lat)), 0.01)
            drone_state.lng += (speed_mps * roll_norm) / (111_000 * cos_lat)

            magnitude = min(math.sqrt(pitch_norm**2 + roll_norm**2), 1.0)
            current_speed = round(speed_mps * magnitude, 1)

        else:
            source = "sim"
            row = step // steps_per_cycle
            pos_in_cycle = step % steps_per_cycle

            if pos_in_cycle < steps_horizontal:
                frac = pos_in_cycle / spc
                lat = BASE_LAT + (row + 0.5) * CELL_LAT
                if row % 2 == 0:
                    lng = BASE_LNG + (0.5 + frac) * CELL_LNG
                else:
                    lng = BASE_LNG + (cols - 0.5 - frac) * CELL_LNG
            else:
                v_frac = (pos_in_cycle - steps_horizontal + 1) / spc
                lat = BASE_LAT + (row + 0.5 + v_frac) * CELL_LAT
                if row % 2 == 0:
                    lng = BASE_LNG + (cols - 0.5) * CELL_LNG
                else:
                    lng = BASE_LNG + 0.5 * CELL_LNG

            drone_state.lat = lat
            drone_state.lng = lng
            step += 1
            current_speed = DRONE_SPEED_MPS

        battery = max(0, battery - 0.05)
        drone_state.battery = battery
        drone_state.status = "flying"
        drone_state.last_update = time.time()

        yield {
            "type": "telemetry",
            "data": {
                "position": {
                    "lat": drone_state.lat,
                    "lng": drone_state.lng,
                    "altitude": drone_state.altitude,
                    "timestamp": int(time.time() * 1000)
                },
                "battery": round(battery, 1),
                "status": "flying",
                "speed": current_speed,
                "elapsed": elapsed,
                "source": source
            }
        }

        await asyncio.sleep(1)