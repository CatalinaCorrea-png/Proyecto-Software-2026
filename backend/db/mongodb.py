from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from core.config import MONGODB_URL, MONGODB_DB

client: AsyncIOMotorClient = None
db = None
gridfs: AsyncIOMotorGridFSBucket = None


async def connect():
    global client, db, gridfs
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]
    gridfs = AsyncIOMotorGridFSBucket(db)
    await _ensure_indexes()
    print(f"✅ MongoDB conectado: {MONGODB_DB}")


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
