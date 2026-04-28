"""
persistence/services/image_service.py
Handles physical file storage (local disk or S3).
The DB only ever stores a path/key — never raw bytes.
"""
from __future__ import annotations
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from persistence.models import Image, Detection


# ─────────────────────────────────────────────────────────────
# LOCAL STORAGE
# ─────────────────────────────────────────────────────────────
async def _save_local(image_bytes: bytes, key: str) -> int:
    """Write bytes to disk. Returns file size."""
    full_path = Path(settings.IMAGES_LOCAL_ROOT) / key
    full_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(full_path, "wb") as f:
        await f.write(image_bytes)
    return len(image_bytes)


def _local_url(key: str) -> str:
    """Return a server-relative URL the frontend can call."""
    return f"/api/images/file/{key}"


# ─────────────────────────────────────────────────────────────
# S3 STORAGE  (only imported when STORAGE_BACKEND=s3)
# ─────────────────────────────────────────────────────────────
async def _save_s3(image_bytes: bytes, key: str) -> int:
    import aioboto3  # pip install aioboto3
    session = aioboto3.Session(
        aws_access_key_id     = settings.AWS_ACCESS_KEY,
        aws_secret_access_key = settings.AWS_SECRET_KEY,
        region_name           = settings.S3_REGION,
    )
    async with session.client("s3") as s3:
        await s3.put_object(
            Bucket      = settings.S3_BUCKET,
            Key         = key,
            Body        = image_bytes,
            ContentType = "image/jpeg",
        )
    return len(image_bytes)


async def _presigned_url_s3(key: str, expires: int = 3600) -> str:
    import aioboto3
    session = aioboto3.Session(
        aws_access_key_id     = settings.AWS_ACCESS_KEY,
        aws_secret_access_key = settings.AWS_SECRET_KEY,
        region_name           = settings.S3_REGION,
    )
    async with session.client("s3") as s3:
        return await s3.generate_presigned_url(
            "get_object",
            Params  = {"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn = expires,
        )


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────
async def store_image(
    db:           AsyncSession,
    detection:    Detection,
    image_bytes:  bytes,
    image_type:   str = "rgb",      # rgb | thermal_overlay | thermal_pure
    mime_type:    str = "image/jpeg",
) -> Image:
    """
    1. Persist bytes to disk or S3
    2. Save an Image record in the DB
    3. Return the ORM Image object
    """
    # Build a deterministic storage key
    # → missions/<mission_id>/detections/<detection_id>/<type>.jpg
    mission_part = str(detection.mission_id) if detection.mission_id else "no-mission"
    key = f"missions/{mission_part}/detections/{detection.id}/{image_type}.jpg"

    backend = settings.STORAGE_BACKEND

    if backend == "local":
        size = await _save_local(image_bytes, key)
        url  = _local_url(key)
    elif backend == "s3":
        size = await _save_s3(image_bytes, key)
        url  = await _presigned_url_s3(key)
    else:
        raise ValueError(f"Unknown STORAGE_BACKEND: {backend}")

    image = Image(
        detection_id    = detection.id,
        image_type      = image_type,
        storage_backend = backend,
        storage_key     = key,
        url             = url,
        file_size_bytes = size,
        mime_type       = mime_type,
    )
    db.add(image)
    await db.flush()
    await db.refresh(image)
    return image


async def get_image_bytes(image: Image) -> bytes:
    """Retrieve raw bytes for a given Image record."""
    if image.storage_backend == "local":
        full_path = Path(settings.IMAGES_LOCAL_ROOT) / image.storage_key
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()
    elif image.storage_backend == "s3":
        import aioboto3
        session = aioboto3.Session(
            aws_access_key_id     = settings.AWS_ACCESS_KEY,
            aws_secret_access_key = settings.AWS_SECRET_KEY,
            region_name           = settings.S3_REGION,
        )
        async with session.client("s3") as s3:
            response = await s3.get_object(Bucket=settings.S3_BUCKET, Key=image.storage_key)
            return await response["Body"].read()
    else:
        raise ValueError(f"Unknown storage_backend: {image.storage_backend}")