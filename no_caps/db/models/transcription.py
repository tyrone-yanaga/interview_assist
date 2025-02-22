# app/db/models/transcription.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from db.session import Base


class TranscriptionStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Transcription(Base):
    """Database model for transcriptions.

    Responsibilities:
    - Define the database schema for transcriptions
    - Define relationships with other models
    - Define basic data validation rules
    """
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(JSON, nullable=True)  # bc transcription mayb pending
    status = Column(
        Enum(TranscriptionStatus),
        default=TranscriptionStatus.PENDING)
    language = Column(String, default="en")
    duration = Column(Integer, nullable=True)  # Duration in seconds
    created_at = Column(DateTime, default=datetime.now())
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    # Foreign keys and relationships
    audio_id = Column(Integer, ForeignKey("audio_files.id"), unique=True)
    audio_file = relationship("Audio", back_populates="transcription")

    # Optional metadata
    word_count = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
