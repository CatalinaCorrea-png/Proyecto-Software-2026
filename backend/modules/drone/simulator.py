import asyncio
import time
from core.state import drone_state, BASE_LAT, BASE_LNG, search_grid
from modules.mapping.grid import CELL_LAT, CELL_LNG, CELL_SIZE_METERS

DRONE_SPEED_MPS = 5.0
SECONDS_PER_CELL = int(CELL_SIZE_METERS / DRONE_SPEED_MPS)

async def simulate_telemetry():
    step = 0
    battery = 100.0
    spc = SECONDS_PER_CELL
    cols = search_grid.cols

    steps_horizontal = cols * spc
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

        battery = max(0, battery - 0.05)
        step += 1

        drone_state.lat = lat
        drone_state.lng = lng
        drone_state.battery = battery
        drone_state.status = "flying"
        drone_state.last_update = time.time()

        yield {
            "type": "telemetry",
            "data": {
                "position": {
                    "lat": lat,
                    "lng": lng,
                    "altitude": 25.0,
                    "timestamp": int(time.time() * 1000)
                },
                "battery": round(battery, 1),
                "status": "flying",
                "speed": 5.0,
                "elapsed": elapsed
            }
        }

        await asyncio.sleep(1)