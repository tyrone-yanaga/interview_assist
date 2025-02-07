# app/api/v1/routers.py
from fastapi import APIRouter
from api.v1.endpoints import user, audio, transcription, playback

api_router = APIRouter()
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(transcription.router, prefix="/transcription", tags=["transcription"])
#api_router.include_router(playback.router, prefix="/playback", tags=["playback"])