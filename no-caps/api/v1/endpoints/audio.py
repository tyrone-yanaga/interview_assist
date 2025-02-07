# app/api/endpoints/audio.py
# Defines routes for uploading audio, fetching transcriptions, and playback

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from db.session import get_db
from services import audio_service
from db.crud import audio as audio_crud

router = APIRouter()


@router.post("/upload/")
async def upload_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await audio_service.process_audio_upload(file, db)


@router.get("/{audio_id}/")
def get_audio(audio_id: int, db: Session = Depends(get_db)):
    return audio_service.get_audio_file(audio_id, db)
