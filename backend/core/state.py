from dataclasses import dataclass, field
import time

#-- Aconcagua
# BASE_LAT = -32.6532
# BASE_LNG = -70.0109

#-- Plaza de Mayo
BASE_LAT = -34.6083
BASE_LNG = -58.3712

@dataclass
class DroneState:
    lat: float = BASE_LAT
    lng: float = BASE_LNG
    altitude: float = 25.0
    battery: float = 100.0
    status: str = "idle"
    last_update: float = field(default_factory=time.time)
    mission_start: float = field(default_factory=time.time)  # ← para tomar tiempo de la mision

drone_state = DroneState()