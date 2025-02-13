# app/db/crud/audio.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from db.models.audio import Audio
from typing import List


def create_audio(
    db: Session, filename: str, file_path: str, duration: int, user_id: int
):
    db_audio = Audio(
        filename=filename,
        file_path=file_path,
        duration=duration,
        user_id=user_id,
    )
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio


def get_user_audio_files(user_id: int, db: Session) -> List[Audio]:
    return db.query(Audio).filter(Audio.user_id == user_id).all()


def get_audio_or_404(db: Session, audio_id: int, user_id: int) -> Audio:
    """
    Retrieve an audio file by its ID and user ID. If the audio does not exist
    or does not belong to the user, raise an HTTP 404 error.

    Args:
        db (Session): SQLAlchemy database session.
        audio_id (int): The ID of the audio file to retrieve.
        user_id (int): The ID of the user who owns the audio file.

    Returns:
        Audio: The retrieved audio object.

    Raises:
        HTTPException: 404 error if the audio is not found or does not belong
        to the user.
    """
    # Query the database for the audio file
    audio = db.query(Audio).filter(Audio.id == audio_id).first()

    # Check if the audio exists and belongs to the specified user
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio with ID {audio_id} not found."
        )
    if audio.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio with ID {audio_id} isn't asoc to user_id {user_id}."
        )

    return audio
