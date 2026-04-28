"""
REST endpoints for images — upload, query by detection, and serve local files.
"""
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from persistence.models import Image
from persistence.schemas import ImageResponse
from persistence.services.image_service import store_image, get_image_bytes

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/upload", response_model=ImageResponse, status_code=201)
async def upload_image(
    detection_id: UUID       = Form(...),
    image_type:   str        = Form("rgb"),
    file:         UploadFile = File(...),
    db:           AsyncSession = Depends(get_db),
):
    """
    Multipart upload: POST /api/images/upload
    Used when the frontend or an external tool wants to attach an image
    to an existing detection.
    """
    from persistence.repositories.detection_repo import get_detection
    detection = await get_detection(db, detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    image_bytes = await file.read()
    image = await store_image(
        db, detection, image_bytes,
        image_type = image_type,
        mime_type  = file.content_type or "image/jpeg",
    )
    return image


@router.get("/detection/{detection_id}", response_model=list[ImageResponse])
async def get_images_for_detection(
    detection_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return all image records linked to a detection."""
    result = await db.execute(
        select(Image).where(Image.detection_id == detection_id)
    )
    return list(result.scalars().all())


@router.get("/file/{path:path}")
async def serve_local_image(path: str):
    """
    Serve a locally stored image.
    The frontend calls /api/images/file/<storage_key>.
    Only active when STORAGE_BACKEND=local.
    """
    if settings.STORAGE_BACKEND != "local":
        raise HTTPException(status_code=404, detail="Local storage not active")

    full_path = Path(settings.IMAGES_LOCAL_ROOT) / path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(str(full_path), media_type="image/jpeg")


@router.get("/{image_id}/download")
async def download_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Stream the raw bytes of any image regardless of backend."""
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    from fastapi.responses import Response
    data = await get_image_bytes(image)
    return Response(content=data, media_type=image.mime_type)