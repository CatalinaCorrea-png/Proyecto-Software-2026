from typing import Optional
from fastapi import APIRouter, Query
import db.mongodb as _mongo

router = APIRouter(prefix="/api/missions", tags=["missions-mongo"])


@router.get("/{mission_id}/detections")
async def list_detections(
    mission_id: str,
    confidence: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, le=200),
):
    query: dict = {"mission_id": mission_id}
    if confidence:
        query["confidence"] = confidence

    skip = (page - 1) * page_size
    total = await _mongo.db.detections.count_documents(query)
    cursor = (
        _mongo.db.detections.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(page_size)
    )
    docs = await cursor.to_list(length=page_size)

    def to_resp(d: dict) -> dict:
        coords = d["coordinates"]["coordinates"]
        return {
            "id": str(d["_id"]),
            "mission_id": d["mission_id"],
            "image_id": str(d["image_id"]),
            "timestamp": d["timestamp"],
            "lat": coords[1],
            "lng": coords[0],
            "altitude_m": d["altitude_m"],
            "confidence": d["confidence"],
            "confidence_score": d["confidence_score"],
            "source": d["source"],
            "temperature_celsius": d.get("temperature_celsius"),
            "bounding_box": d["bounding_box"],
        }

    return {"items": [to_resp(d) for d in docs], "total": total, "page": page}


@router.get("/{mission_id}/stats")
async def mission_stats(mission_id: str):
    doc = await _mongo.db.missions.find_one({"mission_id": mission_id})
    if not doc:
        return {
            "mission_id": mission_id,
            "stats": {"image_count": 0, "detection_count": 0, "coverage_percent": 0},
        }
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/")
async def list_missions(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
):
    query: dict = {}
    if status:
        query["status"] = status

    skip = (page - 1) * page_size
    total = await _mongo.db.missions.count_documents(query)
    cursor = (
        _mongo.db.missions.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    docs = await cursor.to_list(length=page_size)
    for d in docs:
        d["_id"] = str(d["_id"])
    return {"items": docs, "total": total, "page": page}
