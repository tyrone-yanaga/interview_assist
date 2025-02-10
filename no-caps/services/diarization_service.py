
# app/services/diarization_service.py
from pyannote.audio import Pipeline
from core.config import settings


async def perform_diarization(audio_path: str):
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization",
        use_auth_token=settings.HUGGINGFACE_TOKEN
    )

    diarization = pipeline(audio_path)
    return diarization
