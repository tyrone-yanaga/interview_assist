# app/db/models/audio.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.session import Base


class Audio(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    duration = Column(Integer)
    created_at = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="audio_files")
    transcription = relationship("Transcription", back_populates="audio_file")
