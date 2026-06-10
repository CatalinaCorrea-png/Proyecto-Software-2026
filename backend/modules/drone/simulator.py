import time
from core.state import drone_state


def get_current_telemetry() -> dict:
    """Devuelve el último mensaje de telemetría generado por la simulación."""
    if hasattr(drone_state, '_last_telemetry') and drone_state._last_telemetry:
        return drone_state._last_telemetry
    elapsed = int(time.time() - drone_state.mission_start)
    return {
        "type": "telemetry",
        "data": {
            "position": {
                "lat": drone_state.lat,
                "lng": drone_state.lng,
                "altitude": drone_state.altitude,
                "timestamp": int(time.time() * 1000)
            },
            "battery": round(drone_state.battery, 1),
            "status": drone_state.status,
            "speed": 0.0,
            "elapsed": elapsed,
            "sweep_state": drone_state.sweep_state,
            "paused": drone_state.sweep_paused,
            "pending_detection": drone_state.pending_detection,
            "revisit_queue": drone_state.revisit_queue,
        }
    }
