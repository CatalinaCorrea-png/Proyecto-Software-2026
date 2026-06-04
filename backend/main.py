import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import DRONE_UDP_TX_PORT
from db.database import init_db
from db.mission_ops import close_orphan_missions
from db.mongodb import connect as mongo_connect, disconnect as mongo_disconnect
from modules.drone.frame_grabber import stop_grabber
from modules.drone.udp_telemetry import hw_watchdog, start_udp_listener
from routers import images, missions_mongo, stats
from routers import drone, missions_sql, websockets

init_db()
close_orphan_missions()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo_connect()
    # Se guarda el transport para cerrarlo en el shutdown.
    # Sin esto, el socket UDP quedaba ocupado al reiniciar y el puerto
    # lanzaba WinError 10048 en el siguiente arranque.
    udp_transport = await start_udp_listener(DRONE_UDP_TX_PORT)
    asyncio.create_task(hw_watchdog())
    asyncio.create_task(drone.keepalive_loop())
    yield
    udp_transport.close()  # libera el puerto UDP al cerrar
    stop_grabber()
    try:
        await mongo_disconnect()
    except Exception:
        pass


app = FastAPI(title="AeroSearch AI", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drone.router)
app.include_router(missions_sql.router)
app.include_router(websockets.router)
app.include_router(images.router)
app.include_router(missions_mongo.router)
app.include_router(stats.router)


@app.get("/")
def health():
    return {"status": "AeroSearch AI online"}
