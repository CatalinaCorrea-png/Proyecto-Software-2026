import io
import base64
from datetime import datetime
from typing import Optional
import cv2
import numpy as np
from bson import ObjectId

import db.mongodb as _mongo          # import del módulo, no de los valores
from modules.storage.schemas import ImageUploadRequest

THUMBNAIL_WIDTH   = 200
THUMBNAIL_HEIGHT  = 150
THUMBNAIL_QUALITY = 60


def _make_thumbnail(jpeg_bytes: bytes) -> str:
    arr = np.frombuffer(jpeg_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    thumb = cv2.resize(img, (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), interpolation=cv2.INTER_AREA)
    _, buf = cv2.imencode(".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, THUMBNAIL_QUALITY])
    return base64.b64encode(buf.tobytes()).decode()


async def save_image(jpeg_bytes: bytes, meta: ImageUploadRequest) -> dict:
    if _mongo.gridfs is None or _mongo.db is None:
        print("⚠️  MongoDB no disponible, imagen descartada")
        return {}

    # 1. GridFS: imagen full-res
    filename = f"{meta.mission_id}_{meta.timestamp.isoformat()}.jpg"
    gridfs_id = await _mongo.gridfs.upload_from_stream(
        filename,
        io.BytesIO(jpeg_bytes),
        metadata={
            "mission_id": meta.mission_id,
            "timestamp": meta.timestamp,
            "content_type": "image/jpeg",
        },
    )

    # 2. Thumbnail embebido en el documento
    thumbnail_b64 = _make_thumbnail(jpeg_bytes)

    # 3. Documento principal en la colección images
    image_doc = {
        "mission_id": meta.mission_id,
        "gridfs_id": gridfs_id,
        "thumbnail_b64": thumbnail_b64,
        "timestamp": meta.timestamp,
        "coordinates": {
            "type": "Point",
            "coordinates": [meta.lng, meta.lat],    # GeoJSON: [lng, lat]
        },
        "altitude_m": meta.altitude_m,
        "camera": {
            "source": meta.camera_source,
            "view_mode": meta.view_mode,
            "width": 640,
            "height": 480,
            "quality": 60,
            "size_bytes": len(jpeg_bytes),
        },
        "has_detections": len(meta.detections) > 0,
        "detection_count": len(meta.detections),
        "detection_ids": [],
        "created_at": datetime.utcnow(),
    }
    result = await _mongo.db.images.insert_one(image_doc)
    image_id = result.inserted_id

    # 4. Detecciones en colección separada (para queries cross-mission)
    if meta.detections:
        det_docs = [
            {
                "mission_id": meta.mission_id,
                "image_id": image_id,
                "timestamp": meta.timestamp,
                "coordinates": {
                    "type": "Point",
                    "coordinates": [meta.lng, meta.lat],
                },
                "altitude_m": meta.altitude_m,
                "confidence": d.confidence,
                "confidence_score": d.confidence_score,
                "source": d.source,
                "temperature_celsius": d.temperature_celsius,
                "bounding_box": d.bounding_box.model_dump(),
                "created_at": datetime.utcnow(),
            }
            for d in meta.detections
        ]
        det_result = await _mongo.db.detections.insert_many(det_docs)
        await _mongo.db.images.update_one(
            {"_id": image_id},
            {"$set": {"detection_ids": det_result.inserted_ids}},
        )

    # 5. Actualizar stats de la misión (upsert por si no existe aún)
    await _mongo.db.missions.update_one(
        {"mission_id": meta.mission_id},
        {
            "$inc": {
                "stats.image_count": 1,
                "stats.detection_count": len(meta.detections),
            },
            "$setOnInsert": {
                "mission_id": meta.mission_id,
                "status": "active",
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )

    image_doc["_id"] = image_id
    return image_doc


async def get_full_image(image_id: str) -> Optional[bytes]:
    if _mongo.db is None or _mongo.gridfs is None:
        return None
    doc = await _mongo.db.images.find_one({"_id": ObjectId(image_id)})
    if not doc:
        return None
    stream = await _mongo.gridfs.open_download_stream(doc["gridfs_id"])
    return await stream.read()
