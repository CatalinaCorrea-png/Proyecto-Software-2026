import asyncio
import socket
import time

from fastapi import APIRouter
from pydantic import BaseModel

from core.config import DRONE_IP, DRONE_UDP_PORT
from core.detectors import yolo
from core.state import drone_state

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
            try:
                _udp_sock.sendto(b"T:0,Y:0,P:0,R:0", (DRONE_IP, DRONE_UDP_PORT))
            except Exception:
                pass


@router.post("/drone/control")
def drone_control(cmd: DroneCommand):
    global _last_cmd_time
    _last_cmd_time = time.time()
    drone_state.cmd_throttle = cmd.throttle
    drone_state.cmd_pitch = cmd.pitch
    drone_state.cmd_roll = cmd.roll
    payload = f"T:{cmd.throttle},Y:{cmd.yaw},P:{cmd.pitch},R:{cmd.roll}"
    _udp_sock.sendto(payload.encode(), (DRONE_IP, DRONE_UDP_PORT))
    _last_cmd_time = time.time()
    return {"sent": payload, "target": f"{DRONE_IP}:{DRONE_UDP_PORT}"}


@router.post("/drone/reverse")
def drone_reverse():
    drone_state.sim_direction = -1 if drone_state.sim_direction >= 0 else 1
    return {"direction": drone_state.sim_direction}


@router.post("/drone/hover")
def drone_hover():
    if drone_state.sim_direction == 0:
        drone_state.sim_direction = 1
        return {"status": "resumed", "direction": 1}
    drone_state.sim_direction = 0
    drone_state.cmd_throttle = 0
    drone_state.cmd_pitch = 0
    drone_state.cmd_roll = 0
    return {"status": "hover"}


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
