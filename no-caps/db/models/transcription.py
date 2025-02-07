# app/db/models/transcription.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from db.session import Base
from pydantic import BaseModel


class TimestampModel(Base):
    __tablename__ = "timestamps"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transcription_id = Column(String, ForeignKey("transcriptions.TranscriptionID"))
    start = Column(String, nullable=False)
    end = Column(String, nullable=False)
    text = Column(String, nullable=False)


class ConfidenceScoreModel(Base):
    __tablename__ = "confidence_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transcription_id = Column(String, ForeignKey("transcriptions.TranscriptionID"))
    text = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)


class MetadataModel(Base):
    __tablename__ = "metadata"
    TranscriptionID = Column(
        String, ForeignKey("transcriptions.TranscriptionID"), primary_key=True
    )
    CreatedAt = Column(DateTime, nullable=False)
    UpdatedAt = Column(DateTime, nullable=False)
    Source = Column(String, nullable=False)
    Duration = Column(Integer, nullable=False)
    TranscriptionEngine = Column(String, nullable=False)
    Status = Column(String, nullable=False)
    UserID = Column(String, nullable=False)
    Tags = Column(JSON)


class SpeakerDB(Base):
    __tablename__ = "speakers"
    SpeakerID = Column(String, primary_key=True)
    Name = Column(String, nullable=False)
    Role = Column(String, nullable=False)
    TranscriptionID = Column(String, ForeignKey("transcriptions.TranscriptionID"))
    transcription = relationship("TranscriptionDB", back_populates="speakers")


class TranscriptionDB(Base):
    __tablename__ = "transcriptions"
    TranscriptionID = Column(String, primary_key=True)
    AudioFileID = Column(String, nullable=False)
    Text = Column(String, nullable=False)
    SpeakerLabels = Column(JSON)
    Language = Column(String, nullable=False)
    Format = Column(String, nullable=False)
    metadata = relationship("MetadataModel", uselist=False, backref="transcription")
    timestamps = relationship("TimestampModel", backref="transcription")
    confidence_scores = relationship("ConfidenceScoreModel", backref="transcription")
    speakers = relationship(
        "SpeakerDB", order_by=SpeakerDB.SpeakerID, back_populates="transcription"
    )
