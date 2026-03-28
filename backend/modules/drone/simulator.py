import asyncio
import time
from core.state import drone_state, BASE_LAT, BASE_LNG

# Simula un dron que vuela en zigzag sobre una grilla de 20x20 celdas, enviando telemetría cada segundo.
# Es un generador asincrono que se puede usar en el websocket de misión para enviar datos de posición y batería.
async def simulate_telemetry():
    step = 0
    battery = 100.0

    while True:
        elapsed = int(time.time() - drone_state.mission_start)
        # ── Si la batería llegó a 0, detener la misión ───────────────────
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
                    "elapsed": elapsed   # ← segundos desde inicio
                }
            }
            return  # ← termina el generador, no sigue volando

        row = step // 20
        col = step % 20
        if row % 2 == 1:
            col = 19 - col

        lat = BASE_LAT + (row * 0.0002)
        lng = BASE_LNG + (col * 0.0003)
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
                "elapsed": elapsed   # ← segundos desde inicio

            }
        }

        await asyncio.sleep(1)