from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


# Transcription Status Enum
class TranscriptionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    audio_files: List["Audio"] = []

    class Config:
        from_attributes = True


# Audio Schemas
class AudioBase(BaseModel):
    filename: str
    file_path: str
    duration: Optional[int] = None


class AudioCreate(AudioBase):
    user_id: int


class Audio(AudioBase):
    id: int
    created_at: datetime
    user_id: int
    owner: User
    transcription: Optional["Transcription"] = None

    class Config:
        from_attributes = True


# Transcription Schemas
class TranscriptionBase(BaseModel):
    language: str = "en"
    content: Optional[Dict[str, Any]] = None
    status: TranscriptionStatus = TranscriptionStatus.PENDING


class TranscriptionCreate(TranscriptionBase):
    audio_id: int


class Transcription(TranscriptionBase):
    id: int
    duration: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    audio_id: int
    word_count: Optional[int] = None
    confidence_score: Optional[float] = None
    audio_file: Audio

    class Config:
        from_attributes = True


# Update Schemas
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class AudioUpdate(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    duration: Optional[int] = None


class TranscriptionUpdate(BaseModel):
    language: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    status: Optional[TranscriptionStatus] = None
    duration: Optional[int] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    word_count: Optional[int] = None
    confidence_score: Optional[float] = None


# Response Models
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True


class AudioResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    duration: Optional[int]
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True


class TranscriptionResponse(BaseModel):
    id: int
    content: Optional[Dict[str, Any]]
    status: TranscriptionStatus
    language: str
    duration: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    audio_id: int
    word_count: Optional[int]
    confidence_score: Optional[float]

    class Config:
        from_attributes = True


# List Response Models
class UserList(BaseModel):
    items: List[UserResponse]
    total: int


class AudioList(BaseModel):
    items: List[AudioResponse]
    total: int


class TranscriptionList(BaseModel):
    items: List[TranscriptionResponse]
    total: int
