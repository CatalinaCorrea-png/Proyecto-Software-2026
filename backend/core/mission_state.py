import asyncio

grid_clients: list = []
detection_history: list[dict] = []
active_mission_id: int | None = None
simulation_task: asyncio.Task | None = None
mission_configured: bool = False
mission_name: str = ""
mission_altitude: float | None = None
mission_cell_size_m: float | None = None
