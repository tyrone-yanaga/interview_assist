
# app/api/v1/endpoints/transcription.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from services import transcription_service

router = APIRouter()


@router.post("/{audio_id}/transcribe/")
async def transcribe_audio(audio_id: int, db: Session = Depends(get_db)):
    return await transcription_service.transcribe_audio(audio_id, db)

