# app/api/v1/routers.py
from fastapi import APIRouter
from api.v1.endpoints import user, audio, transcription, auth

# Create main v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(
    user.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    audio.router,
    prefix="/audio",
    tags=["audio"]
)

api_router.include_router(
    transcription.router,
    prefix="/transcriptions",  # Note: plural form
    tags=["transcriptions"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)