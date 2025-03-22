# app/api/v1/endpoints/transcription.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from db.session import get_db
from services.transcription_service import TranscriptionService
from db.models.transcription import TranscriptionStatus
from db.crud.transcription import TranscriptionCRUD
from db.crud.audio import get_audio_or_404
from db.models.user import User
from core.auth import get_current_user

router = APIRouter()
transcription_service = TranscriptionService()


@router.post("/transcribe/{audio_id}")
async def create_transcription(
    audio_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Endpoint to create a new transcription job.

    Responsibilities:
    - Handle HTTP requests
    - Validate input
    - Manage authentication/authorization
    - Delegate to service layer
    - Return appropriate HTTP responses
    """

    # Check if audio exists and user has access
    audio = get_audio_or_404(db, audio_id, current_user.id)

    # Create transcription job
    transcription = await transcription_service.create_transcription_job(
        db,
        audio_id=audio_id,
        language="en"
    )

    # Add to background tasks
    background_tasks.add_task(
        transcription_service.process_transcription,
        db,
        transcription.id,
        audio.file_path
    )

    return {
        "message": "Transcription job created",
        "transcription_id": transcription.id,
        "status": transcription.status
    }


@router.get("/transcription/{transcription_id}")
async def get_transcription_status(
    transcription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get transcription status and results."""
    transcription = TranscriptionCRUD.get_transcription(db, transcription_id)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    # Check user has access to this transcription
    if not TranscriptionService.has_access_to_transcription(
            db=db,
            transcription=transcription,
            user_id=current_user.id):

        raise HTTPException(status_code=403, detail="Not authorized")

    response = {
        "id": transcription.id,
        "status": transcription.status,
        "created_at": transcription.created_at
    }

    # Include additional data if completed
    if transcription.status == TranscriptionStatus.COMPLETED:
        response.update({
            "content": transcription.content,
            "word_count": transcription.word_count,
            "confidence_score": transcription.confidence_score,
            "completed_at": transcription.completed_at
        })
    # Include error if failed
    elif transcription.status == TranscriptionStatus.FAILED:
        response["error"] = transcription.error_message

    return response


@router.put("/transcription/{transcription_id}")
async def update_transcription(
    transcription_id: int,
    transcription_update: Dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Update a transcription."""

    # Check user has access to this transcription
    if not TranscriptionService.has_access_to_transcription(
            db=db,
            transcription=transcription_id,
            user_id=current_user.id):

        raise HTTPException(status_code=403, detail="Not authorized")

    updated_transcription = await TranscriptionCRUD.update_transcription_content(
        db,
        transcription_id,
        transcription_update)

    if not updated_transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    response = {
        "id": updated_transcription.id,
        "status": updated_transcription.status,
        "created_at": updated_transcription.created_at
    }

    return response
