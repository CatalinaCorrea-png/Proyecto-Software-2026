import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from core.config import MONGODB_URL, MONGODB_DB

client: AsyncIOMotorClient = None
db = None
gridfs: AsyncIOMotorGridFSBucket = None

# Número máximo de intentos y tiempo de espera entre cada uno.
# Necesario porque MongoDB (especialmente en Docker) puede tardar unos segundos
# en estar listo para aceptar conexiones después de iniciarse.
_MAX_RETRIES = 5
_RETRY_DELAY = 3  # segundos entre intentos


async def connect():
    global client, db, gridfs
    # Intenta conectarse hasta _MAX_RETRIES veces antes de lanzar error.
    # serverSelectionTimeoutMS=5000 limita cada intento a 5s en lugar del
    # default de 30s, para que el ciclo completo no bloquee demasiado tiempo.
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            db = client[MONGODB_DB]
            gridfs = AsyncIOMotorGridFSBucket(db)
            await _ensure_indexes()
            print(f"✅ MongoDB conectado: {MONGODB_DB}")
            return
        except Exception as e:
            print(f"⚠️  MongoDB intento {attempt}/{_MAX_RETRIES} fallido: {e}")
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_DELAY)
    raise RuntimeError(f"No se pudo conectar a MongoDB tras {_MAX_RETRIES} intentos")


async def disconnect():
    if client:
        client.close()
        print("❌ MongoDB desconectado")


async def _ensure_indexes():
    await db.images.create_index([("coordinates", "2dsphere")])
    await db.images.create_index([("mission_id", 1), ("timestamp", -1)])
    await db.images.create_index([("has_detections", 1), ("mission_id", 1)])
    await db.detections.create_index([("coordinates", "2dsphere")])
    await db.detections.create_index([("mission_id", 1), ("timestamp", -1)])
    await db.detections.create_index([("image_id", 1)])
    await db.missions.create_index([("mission_id", 1)], unique=True)
