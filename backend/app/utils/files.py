"""File upload and deletion helpers."""
import os
import uuid
import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def save_upload_file(upload_file: UploadFile, subfolder: str = "products") -> str:
    """Save an uploaded image file securely and return its relative path."""
    if upload_file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type {upload_file.content_type}. Allowed: JPEG, PNG, WebP.",
        )

    _, ext = os.path.splitext(upload_file.filename or "")
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    target_dir = os.path.join(settings.UPLOADS_DIR, subfolder)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, unique_filename)

    file_size = 0
    async with aiofiles.open(target_path, "wb") as out_file:
        while content := await upload_file.read(1024 * 64):  # 64 KB chunks
            file_size += len(content)
            if file_size > MAX_FILE_SIZE:
                # Remove partially written file
                try:
                    os.remove(target_path)
                except OSError:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File exceeds maximum size limit of 10MB.",
                )
            await out_file.write(content)

    # Return relative path for web serving, e.g. "products/abc.jpg"
    return f"{subfolder}/{unique_filename}"


async def delete_file(relative_path: str) -> bool:
    """Delete a stored file by relative path."""
    if not relative_path:
        return False
    full_path = os.path.join(settings.UPLOADS_DIR, relative_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
            return True
        except OSError:
            return False
    return False

