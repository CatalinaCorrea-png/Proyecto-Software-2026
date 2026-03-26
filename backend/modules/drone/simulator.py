import asyncio
import time
import random
from core.state import drone_state  # ← importar estado compartido

BASE_LAT = -34.6083
BASE_LNG = -58.3712

async def simulate_telemetry():
    step = 0
    battery = 100.0

    while True:
        row = step // 20
        col = step % 20
        if row % 2 == 1:
            col = 19 - col

        lat = BASE_LAT + (row * 0.0002)
        lng = BASE_LNG + (col * 0.0003)
        battery = max(0, battery - 0.05)
        step += 1

        # ── NUEVO: actualizar estado global ──────────────────────────────
        drone_state.lat = lat
        drone_state.lng = lng
        drone_state.battery = battery
        drone_state.status = "flying"
        drone_state.last_update = time.time()
        # ─────────────────────────────────────────────────────────────────

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
                "speed": 5.0
            }
        }

        await asyncio.sleep(1)