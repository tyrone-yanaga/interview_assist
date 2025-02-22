from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging
from db.session import get_db
from db.schemas import UserCreate, UserResponse, UserList, User
from db.crud.user import create_user
from . import schemas, models

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create routers
user_router = APIRouter(prefix="/users", tags=["users"])
audio_router = APIRouter(prefix="/audio", tags=["audio"])
transcription_router = APIRouter(
    prefix="/transcriptions", tags=["transcriptions"])


# User routes

@user_router.post("/", response_model=UserResponse)
async def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.debug(f"Received create user request for email: {user.email}")
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.debug(f"User with email {user.email} already exists")
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        db_user = create_user(db=db, user=user)
        logger.debug(f"Successfully created user with id: {db_user.id}")
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise


@user_router.get("", response_model=UserList)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()
    return {"items": users, "total": total}


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Audio routes
@audio_router.get("", response_model=schemas.AudioList)
async def list_audio_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Audio)
    if user_id:
        query = query.filter(models.Audio.user_id == user_id)

    audio_files = query.offset(skip).limit(limit).all()
    total = query.count()
    return {"items": audio_files, "total": total}


@audio_router.get("/{audio_id}", response_model=schemas.AudioResponse)
async def get_audio(audio_id: int, db: Session = Depends(get_db)):
    audio = db.query(models.Audio).filter(models.Audio.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return audio


# Transcription routes
@transcription_router.get("", response_model=schemas.TranscriptionList)
async def list_transcriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[schemas.TranscriptionStatus] = None,
    audio_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Transcription)

    if status:
        query = query.filter(models.Transcription.status == status)
    if audio_id:
        query = query.filter(models.Transcription.audio_id == audio_id)

    transcriptions = query.offset(skip).limit(limit).all()
    total = query.count()
    return {"items": transcriptions, "total": total}


@transcription_router.get(
    "/{transcription_id}", response_model=schemas.TranscriptionResponse
)
async def get_transcription(
        transcription_id: int, db: Session = Depends(get_db)):
    transcription = (
        db.query(models.Transcription)
        .filter(models.Transcription.id == transcription_id)
        .first()
    )
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return transcription


# Include these routers in your main FastAPI app:
"""
app = FastAPI()
app.include_router(user_router)
app.include_router(audio_router)
app.include_router(transcription_router)
"""
