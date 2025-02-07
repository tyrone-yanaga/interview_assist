# app/db/crud/audio.py
from sqlalchemy.orm import Session
from app.db.models.audio import Audio
from typing import List


def create_audio(
    db: Session, filename: str, file_path: str, duration: int, user_id: int
):
    db_audio = Audio(
        filename=filename, file_path=file_path, duration=duration, user_id=user_id
    )
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio


def get_user_audio_files(db: Session, user_id: int) -> List[Audio]:
    return db.query(Audio).filter(Audio.user_id == user_id).all()
