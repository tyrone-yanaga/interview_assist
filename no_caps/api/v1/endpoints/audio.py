# app/api/endpoints/audio.py
# Defines routes for uploading audio, fetching transcriptions, and playback

from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from services import audio_service
from core.auth import get_current_user
from db.models import User

router = APIRouter()


@router.post("/upload/")
async def upload_audio(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await audio_service.process_audio_upload(file, db, current_user)


@router.get("/{user_id}/")
async def get_audio(user_id: int, db: Session = Depends(get_db)):
    return await audio_service.get_audio_files(user_id=user_id, db=db)
