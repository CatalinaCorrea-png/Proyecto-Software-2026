import asyncio
import socket
import time

from fastapi import APIRouter
from pydantic import BaseModel

from core.config import DRONE_IP, DRONE_UDP_PORT, APIDRONE_API_URL
from core.detectors import yolo
from core.state import drone_state
from services.apidrone_client import get_client as get_apidrone

router = APIRouter(tags=["drone"])

_udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_last_cmd_time: float = 0.0


class DroneCommand(BaseModel):
    throttle: int = 0
    yaw: int = 0
    pitch: int = 0
    roll: int = 0


async def keepalive_loop() -> None:
    while True:
        await asyncio.sleep(2.0)
        if time.time() - _last_cmd_time > 3.0:
            client = get_apidrone()
            if client is not None:
                await client.send_axes(0, 0, 0, 0)
            elif DRONE_IP:
                try:
                    _udp_sock.sendto(b"T:0,Y:0,P:0,R:0", (DRONE_IP, DRONE_UDP_PORT))
                except Exception:
                    pass


@router.post("/drone/control")
async def drone_control(cmd: DroneCommand):
    global _last_cmd_time
    _last_cmd_time = time.time()
    drone_state.cmd_throttle = cmd.throttle
    drone_state.cmd_pitch = cmd.pitch
    drone_state.cmd_roll = cmd.roll

    client = get_apidrone()
    if client is not None:
        await client.send_axes(cmd.throttle, cmd.yaw, cmd.pitch, cmd.roll)
        return {"driver": "apidrone", "throttle": cmd.throttle, "yaw": cmd.yaw,
                "pitch": cmd.pitch, "roll": cmd.roll}

    payload = f"T:{cmd.throttle},Y:{cmd.yaw},P:{cmd.pitch},R:{cmd.roll}"
    _udp_sock.sendto(payload.encode(), (DRONE_IP, DRONE_UDP_PORT))
    return {"sent": payload, "target": f"{DRONE_IP}:{DRONE_UDP_PORT}"}


@router.post("/drone/reverse")
def drone_reverse():
    drone_state.sim_direction = -1 if drone_state.sim_direction >= 0 else 1
    return {"direction": drone_state.sim_direction}


@router.post("/drone/hover")
async def drone_hover():
    client = get_apidrone()
    if drone_state.sim_direction == 0:
        drone_state.sim_direction = 1
        if client is not None:
            await client.send_axes(0, 0, 0, 0)
        return {"status": "resumed", "direction": 1}
    drone_state.sim_direction = 0
    drone_state.cmd_throttle = 0
    drone_state.cmd_pitch = 0
    drone_state.cmd_roll = 0
    if client is not None:
        await client.send_axes(0, 0, 0, 0)
    return {"status": "hover"}


# Rutas específicas de Apidrone — deben ir ANTES de /drone/{altitude}
@router.post("/drone/takeoff")
async def drone_takeoff():
    client = get_apidrone()
    if client is None:
        return {"status": "not_supported", "driver": "udp"}
    await client.send_takeoff()
    return {"status": "takeoff", "driver": "apidrone"}


@router.post("/drone/land")
async def drone_land():
    client = get_apidrone()
    if client is None:
        return {"status": "not_supported", "driver": "udp"}
    await client.send_land()
    return {"status": "land", "driver": "apidrone"}


@router.post("/drone/estop")
async def drone_estop():
    client = get_apidrone()
    if client is None:
        return {"status": "not_supported", "driver": "udp"}
    await client.send_estop()
    return {"status": "estop", "driver": "apidrone"}


@router.get("/drone/imu")
async def get_imu():
    client = get_apidrone()
    if client is None:
        return {"imu_ok": False, "connected": False, "roll": 0.0, "pitch": 0.0}
    try:
        return await client.get_telemetry()
    except Exception as exc:
        return {"imu_ok": False, "connected": False, "error": str(exc)}


@router.get("/drone/capabilities")
async def get_capabilities():
    client = get_apidrone()
    if client is None:
        return {"driver": "udp"}
    try:
        caps = await client.get_capabilities()
        return {"driver": "apidrone", **caps}
    except Exception as exc:
        return {"driver": "apidrone", "error": str(exc)}


@router.get("/drone/state")
def get_drone_state():
    return {
        "altitude": drone_state.altitude,
        "model": yolo.weights_name,
    }


@router.post("/drone/{altitude}")
def set_altitude(altitude: float):
    drone_state.altitude = max(0.0, altitude)
    return {
        "altitude": drone_state.altitude,
        "model": yolo.weights_name,
    }
