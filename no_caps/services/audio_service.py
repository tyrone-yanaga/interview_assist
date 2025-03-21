# app/services/audio_service.py
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from db.crud import audio as audio_crud
from utils.file_handling import save_upload_file
from utils.audio_processing import get_audio_duration


async def process_audio_upload(file: UploadFile, db: Session):
    if not file.content_type.startswith('audio/'):
        print('FILE CONTENT TYPE:', file.content_type)
        raise HTTPException(
            status_code=400,
            detail="File must be an audio file"
        )
    file_path = await save_upload_file(file)
    duration = get_audio_duration(file_path)

    return audio_crud.create_audio(
        db,
        filename=file.filename,
        file_path=file_path,
        duration=duration,
        user_id=1  # TODO Replace with actual user_id from jwt token
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
