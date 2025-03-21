# app/services/audio_service.py
from fastapi import UploadFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from db.crud import audio as audio_crud
from db.crud.user import get_user_by_id, User
from no_caps.dependencies import get_db
from utils.file_handling import save_upload_file
from utils.audio_processing import get_audio_duration

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
SECRET_KEY = "your_secret_key"  # Replace with your actual secret key
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user

async def process_audio_upload(file: UploadFile, db: Session, current_user: User = Depends(get_current_user)):
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
