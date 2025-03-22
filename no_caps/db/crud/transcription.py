# app/db/crud/transcription.py
from typing import Optional
from sqlalchemy.orm import Session
from db.models.transcription import Transcription, TranscriptionStatus
from datetime import datetime
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class TranscriptionCRUD:
    """CRUD operations for transcriptions.

    Responsibilities:
    - Handle all database operations for transcriptions
    - Implement basic query operations
    - Maintain data integrity
    """

    @staticmethod
    def create_transcription(
        db: Session,
        audio_id: int,
        language: str = "en"
    ) -> Transcription:
        """Create a new transcription record."""
        db_transcription = Transcription(
            audio_id=audio_id,
            language=language,
            status=TranscriptionStatus.PENDING
        )
        db.add(db_transcription)
        db.commit()
        db.refresh(db_transcription)
        return db_transcription

    @staticmethod
    def get_transcription(
        db: Session,
        transcription_id: int
    ) -> Optional[Transcription]:
        """Retrieve a transcription by ID."""
        return db.query(Transcription).filter(
            Transcription.id == transcription_id
        ).first()

    @staticmethod
    def get_transcription_by_id(
        db: Session,
        transcription_id: int
    ) -> Transcription:
        """Get a transcription by its ID."""
        return db.query(Transcription).filter(Transcription.id == transcription_id).first()

    @staticmethod
    def get_transcription_by_audio_id(
        db: Session,
        audio_id: int
    ) -> Optional[Transcription]:
        """Retrieve a transcription by audio ID."""
        try:
            transcription = db.query(Transcription).filter(
                Transcription.audio_id == audio_id
            ).first()
            if not transcription:
                logger.warning(f"No transcription found for audio ID: {audio_id}")
            return transcription
        except Exception as e:
            logger.error(f"Error retrieving transcription for audio ID {audio_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving transcription"
            ) from e

    @staticmethod
    def update_transcription_content(
        db: Session,
        transcription_id: int,
        content: str,
    ) -> Transcription:
        """Update transcription with completed content."""
        transcription = TranscriptionCRUD.get_transcription(
            db, transcription_id)
        if transcription:
            transcription.content = content
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.completed_at = datetime.now()

            db.commit()
            db.refresh(transcription)
        return transcription

    @staticmethod
    def update_transcription_status(
        db: Session,
        transcription_id: int,
        status: TranscriptionStatus,
        error_message: Optional[str] = None
    ) -> Transcription:
        """Update transcription status."""
        transcription = TranscriptionCRUD.get_transcription(
            db, transcription_id)
        if transcription:
            transcription.status = status
            transcription.error_message = error_message
            if status == TranscriptionStatus.COMPLETED:
                transcription.completed_at = datetime.now()
            db.commit()
            db.refresh(transcription)
        return transcription
