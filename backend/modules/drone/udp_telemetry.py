import asyncio
import re
import time
from core.state import drone_state

_PATTERN = re.compile(r'LAT:([-\d.]+),LNG:([-\d.]+),ALT:([-\d.]+)')
_HW_TIMEOUT = 3.0  # segundos sin paquete → desactiva modo hardware


class _Protocol(asyncio.DatagramProtocol):
    def datagram_received(self, data: bytes, _addr):
        m = _PATTERN.search(data.decode(errors='ignore'))
        if not m:
            return
        lat = float(m.group(1))
        lng = float(m.group(2))
        if lat == 0.0 and lng == 0.0:
            return
        drone_state.lat = lat
        drone_state.lng = lng
        drone_state.altitude = float(m.group(3))
        drone_state.last_hw_telemetry = time.time()
        if not drone_state.real_telemetry_active:
            drone_state.real_telemetry_active = True
            print(f"Telemetry active — {drone_state.lat:.6f}, {drone_state.lng:.6f}")

    def error_received(self, exc):
        print(f"⚠️  UDP error: {exc}")


async def start_udp_listener(port: int) -> asyncio.BaseTransport:
    loop = asyncio.get_event_loop()
    transport, _ = await loop.create_datagram_endpoint(
        _Protocol,
        local_addr=('0.0.0.0', port),
    )
    print(f"📡 UDP escuchando telemetría en :{port}")
    return transport


async def hw_watchdog():
    """Marca real_telemetry_active=False si no llegan paquetes en _HW_TIMEOUT segundos."""
    while True:
        await asyncio.sleep(1.0)
        if (
            drone_state.real_telemetry_active
            and time.time() - drone_state.last_hw_telemetry > _HW_TIMEOUT
        ):
            drone_state.real_telemetry_active = False
            print("⚠️  Telemetría hardware perdida, volviendo a simulador")
