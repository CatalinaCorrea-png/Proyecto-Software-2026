import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response
from bson import ObjectId

import db.mongodb as _mongo
from modules.storage.image_service import save_image, get_full_image
from modules.storage.schemas import (
    ImageUploadRequest, DetectionPayload, ImageResponse, ImageListResponse,
)

router = APIRouter(prefix="/api/images", tags=["images"])

PROJECTION = {
    "thumbnail_b64": 1, "mission_id": 1, "timestamp": 1,
    "coordinates": 1, "altitude_m": 1, "camera": 1,
    "has_detections": 1, "detection_count": 1, "detection_ids": 1,
}


def _doc_to_response(doc: dict) -> ImageResponse:
    coords = doc["coordinates"]["coordinates"]   # [lng, lat]
    return ImageResponse(
        id=str(doc["_id"]),
        mission_id=doc["mission_id"],
        timestamp=doc["timestamp"],
        lat=coords[1],
        lng=coords[0],
        altitude_m=doc["altitude_m"],
        view_mode=doc["camera"]["view_mode"],
        has_detections=doc["has_detections"],
        detection_count=doc["detection_count"],
        thumbnail_b64=doc["thumbnail_b64"],
        detection_ids=[str(d) for d in doc.get("detection_ids", [])],
    )


@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    mission_id: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    altitude_m: float = Form(0.0),
    timestamp: Optional[str] = Form(None),
    view_mode: str = Form("rgb"),
    camera_source: str = Form("esp32"),
    detections_json: Optional[str] = Form(None),
):
    jpeg_bytes = await file.read()
    ts = datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()

    detections: list[DetectionPayload] = []
    if detections_json:
        raw = json.loads(detections_json)
        detections = [DetectionPayload(**d) for d in raw]

    meta = ImageUploadRequest(
        mission_id=mission_id,
        lat=lat,
        lng=lng,
        altitude_m=altitude_m,
        timestamp=ts,
        view_mode=view_mode,
        camera_source=camera_source,
        detections=detections,
    )
    doc = await save_image(jpeg_bytes, meta)
    return _doc_to_response(doc)


@router.get("/near/search", response_model=ImageListResponse)
async def images_near(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_m: float = Query(500),
    mission_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
):
    query: dict = {
        "coordinates": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": radius_m,
            }
        }
    }
    if mission_id:
        query["mission_id"] = mission_id

    skip = (page - 1) * page_size
    count_query = {"mission_id": mission_id} if mission_id else {}
    total = await _mongo.db.images.count_documents(count_query)
    cursor = _mongo.db.images.find(query, PROJECTION).skip(skip).limit(page_size)
    docs = await cursor.to_list(length=page_size)
    return ImageListResponse(
        items=[_doc_to_response(d) for d in docs],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{image_id}/full")
async def get_image_full(image_id: str):
    jpeg_bytes = await get_full_image(image_id)
    if not jpeg_bytes:
        raise HTTPException(404, "Image not found")
    return Response(content=jpeg_bytes, media_type="image/jpeg")


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image_meta(image_id: str):
    doc = await _mongo.db.images.find_one({"_id": ObjectId(image_id)})
    if not doc:
        raise HTTPException(404, "Image not found")
    return _doc_to_response(doc)


@router.get("/", response_model=ImageListResponse)
async def list_images(
    mission_id: Optional[str] = Query(None),
    has_detections: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
):
    query: dict = {}
    if mission_id:
        query["mission_id"] = mission_id
    if has_detections is not None:
        query["has_detections"] = has_detections

    skip = (page - 1) * page_size
    total = await _mongo.db.images.count_documents(query)
    cursor = (
        _mongo.db.images.find(query, PROJECTION)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(page_size)
    )
    docs = await cursor.to_list(length=page_size)
    return ImageListResponse(
        items=[_doc_to_response(d) for d in docs],
        total=total, page=page, page_size=page_size,
    )
