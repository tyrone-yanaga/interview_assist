# app/services/transcription_service.py
from http.client import HTTPException
import whisper
from sqlalchemy.orm import Session
from db.crud import audio as audio_crud
from db.crud import transcription as transcription_crud


async def transcribe_audio(audio_id: int, db: Session):
    audio = audio_crud.get_audio(db, audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")

    model = whisper.load_model("base")
    result = model.transcribe(audio.file_path)

    return transcription_crud.create_transcription(
        db, content=result["text"], audio_id=audio_id
    )
