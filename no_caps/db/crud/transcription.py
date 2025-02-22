# app/db/crud/transcription.py
from typing import Optional
from sqlalchemy.orm import Session
from db.models.transcription import Transcription, TranscriptionStatus
from datetime import datetime


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
    def update_transcription_content(
        db: Session,
        transcription_id: int,
        content: str,
        word_count: int,
        confidence_score: float
    ) -> Transcription:
        """Update transcription with completed content."""
        transcription = TranscriptionCRUD.get_transcription(
            db, transcription_id)
        if transcription:
            transcription.content = content
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.completed_at = datetime.now()
            transcription.word_count = word_count
            transcription.confidence_score = confidence_score
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
