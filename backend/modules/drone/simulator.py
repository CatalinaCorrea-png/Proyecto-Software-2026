import asyncio
import math
import time
import random

# Simula el movimiento del drone en un patrón lawnmower
# Centro: Plaza de Mayo Buenos Aires (podés cambiar a donde quieras)
BASE_LAT = -34.6083
BASE_LNG = -58.3712

async def simulate_telemetry():
    """Generador async que yield telemetría cada 1 segundo"""
    step = 0
    battery = 100.0

    while True:
        # Patrón lawnmower simple: zigzag horizontal
        row = step // 20
        col = step % 20
        if row % 2 == 1:
            col = 19 - col  # zigzag

        lat = BASE_LAT + (row * 0.0002)
        lng = BASE_LNG + (col * 0.0003)

        battery = max(0, battery - 0.05)
        step += 1

        """yield convierte una función en un generador — en vez de ejecutarse toda de una 
        y retornar un valor, la función pausa en cada yield y entrega un valor, 
        luego continúa desde donde se quedó."""
        """produce datos de telemetría para siempre hasta que el WebSocket se cierra."""
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

        # Cada ~15 pasos simula una detección
        if step % 15 == 0:
            yield {
                "type": "detection",
                "data": {
                    "id": f"det_{step}",
                    "position": {
                        "lat": lat + random.uniform(-0.0001, 0.0001),
                        "lng": lng + random.uniform(-0.0001, 0.0001),
                        "altitude": 0,
                        "timestamp": int(time.time() * 1000)
                    },
                    "confidence": random.choice(["high", "medium", "low"]),
                    "source": random.choice(["rgb", "thermal", "fusion"]),
                    "temperature": round(random.uniform(34.0, 37.5), 1),
                    "timestamp": int(time.time() * 1000)
                }
            }

        await asyncio.sleep(1)