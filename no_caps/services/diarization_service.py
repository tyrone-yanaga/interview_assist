
# # app/services/diarization_service.py
# from pyannote.audio import Pipeline
# import os
# from dotenv import load_dotenv
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent
# load_dotenv(BASE_DIR / '.env')


# async def perform_diarization(audio_path: str):
#     pipeline = Pipeline.from_pretrained(
#         "pyannote/speaker-diarization",
#         use_auth_token=os.getenv('HUGGINGFACE_TOKEN')
#     )

#     diarization = pipeline(audio_path)
#     return diarization
