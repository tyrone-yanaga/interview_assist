# app/utils/file_handling.py
import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from core.logging import logger

UPLOAD_DIR = Path("uploads")
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}


def ensure_upload_dir():
    """Ensure the upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_file(file: UploadFile) -> str:
    """
    Save an uploaded file to the uploads directory with a unique filename.

    Args:
        file (UploadFile): The uploaded file

    Returns:
        str: Path to the saved file

    Raises:
        HTTPException: If file extension is not allowed or save fails
    """
    ensure_upload_dir()

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_extension} not allowed. Allowed extensions: {ALLOWED_AUDIO_EXTENSIONS}",
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    return str(file_path)


def delete_file(file_path: str) -> bool:
    """
    Delete a file from the filesystem.

    Args:
        file_path (str): Path to the file to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {str(e)}")
        return False
