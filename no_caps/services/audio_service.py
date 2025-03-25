# app/services/audio_service.py
from fastapi import UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from db.crud import audio as audio_crud
from utils.file_handling import save_upload_file
from utils.audio_processing import get_audio_duration
from core.auth import get_current_user
from db.models import User
import logging
logger = logging.getLogger(__name__)


async def process_audio_upload(
    file: UploadFile,
    db: Session,
    current_user: User = Depends(get_current_user)
):
    if not file.content_type.startswith('audio/'):
        print('FILE CONTENT TYPE:', file.content_type)
        raise HTTPException(
            status_code=400,
            detail="File must be an audio file"
        )
    file_path = await save_upload_file(file)
    duration = get_audio_duration(file_path)

    logger.info(f"Saving file to: {file_path}")
    print(f"Saving file to: {file_path}")

    return audio_crud.create_audio(
        db,
        filename=file.filename,
        file_path=file_path,
        duration=duration,
        user_id=current_user.id
    )


async def get_audio_files(user_id: int, db: Session):
    # TODO JWT user_id extraction/verification
    # user_id = content extracted from JWT
    # else no audio return 404

    # if user_id associated to audio_id
    #       (maybe request if a record existstied to user_id&audio_id)
    #   return audio_id
    # else return permission denied
    return audio_crud.get_user_audio_files(db=db, user_id=user_id)
