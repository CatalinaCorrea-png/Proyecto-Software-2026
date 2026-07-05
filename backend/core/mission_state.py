import asyncio

grid_clients: list = []
detection_clients: list = []
mission_clients: list = []
detection_history: list[dict] = []
active_mission_id: int | None = None
simulation_task: asyncio.Task | None = None
detection_task: asyncio.Task | None = None
mission_configured: bool = False
mission_name: str = ""
mission_altitude: float | None = None
mission_cell_size_m: float | None = None


async def broadcast(clients: list, message: str) -> None:
    """Envía un mensaje a todos los clientes, descartando los que ya se cayeron."""
    for client in clients.copy():
        try:
            await client.send_text(message)
        except Exception:
            try:
                clients.remove(client)
            except ValueError:
                pass
