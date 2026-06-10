import asyncio
import json
import logging
from typing import Optional

import httpx
import websockets

from core.config import APIDRONE_API_URL, APIDRONE_WS_URL

logger = logging.getLogger(__name__)


class ApidroneClient:
    def __init__(self):
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._http = httpx.AsyncClient(base_url=APIDRONE_API_URL, timeout=5.0)
        self._running = False
        self._connect_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._running = True
        self._connect_task = asyncio.create_task(self._reconnect_loop())
        logger.info("[apidrone] cliente iniciado → %s", APIDRONE_API_URL)

    async def stop(self) -> None:
        self._running = False
        if self._connect_task:
            self._connect_task.cancel()
            try:
                await self._connect_task
            except asyncio.CancelledError:
                pass
        self._ws = None
        await self._http.aclose()
        logger.info("[apidrone] cliente detenido")

    async def _reconnect_loop(self) -> None:
        delay = 1.0
        while self._running:
            try:
                async with websockets.connect(f"{APIDRONE_WS_URL}/ws") as ws:
                    self._ws = ws
                    logger.info("[apidrone] WS conectado a %s/ws", APIDRONE_WS_URL)
                    delay = 1.0
                    async for _ in ws:
                        pass  # drena mensajes entrantes; sale al desconectar
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("[apidrone] WS error: %s — reintento en %.0fs", exc, delay)
            self._ws = None
            if self._running:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)

    async def _send_ws(self, payload: dict) -> None:
        ws = self._ws
        if ws is None:
            logger.debug("[apidrone] WS no disponible, descartando: %s", payload.get("type"))
            return
        try:
            await ws.send(json.dumps(payload))
        except Exception as exc:
            logger.warning("[apidrone] error en WS send: %s", exc)
            self._ws = None

    async def send_axes(self, throttle: int, yaw: int, pitch: int, roll: int) -> None:
        # throttle: 0-255 → 0.0-1.0 | yaw/pitch/roll: -100..100 → -1.0..1.0
        await self._send_ws({
            "type": "axes",
            "mode": "abs",
            "throttle": min(1.0, throttle / 255.0),
            "yaw":      yaw   / 100.0,
            "pitch":    pitch / 100.0,
            "roll":     roll  / 100.0,
        })

    async def send_takeoff(self) -> None:
        await self._send_ws({"type": "takeoff"})

    async def send_land(self) -> None:
        await self._send_ws({"type": "land"})

    async def send_estop(self) -> None:
        await self._send_ws({"type": "estop"})

    async def get_telemetry(self) -> dict:
        resp = await self._http.get("/telemetry")
        resp.raise_for_status()
        return resp.json()

    async def get_capabilities(self) -> dict:
        resp = await self._http.get("/capabilities")
        resp.raise_for_status()
        return resp.json()

    @property
    def mjpeg_url(self) -> str:
        return f"{APIDRONE_API_URL}/mjpeg"

    @property
    def connected(self) -> bool:
        return self._ws is not None


_instance: Optional[ApidroneClient] = None


def get_client() -> Optional[ApidroneClient]:
    return _instance


def init_client() -> ApidroneClient:
    global _instance
    _instance = ApidroneClient()
    return _instance
