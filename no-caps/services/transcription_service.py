# app/services/transcription_service.py
from http.client import HTTPException
import whisper
from pyannote.audio import Pipeline
from sqlalchemy.orm import Session
from db.crud import audio as audio_crud
from db.crud import transcription as transcription_crud


async def transcribe_audio(audio_id: int, db: Session):
    # Fetch the audio file from the database
    audio = audio_crud.get_audio(db, audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Load the Whisper model for transcription
    whisper_model = whisper.load_model("base")

    # Load the pyannote.audio pipeline for diarization
    diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")

    # Perform diarization
    diarization = diarization_pipeline(audio.file_path)

    # Perform transcription
    transcription_result = whisper_model.transcribe(audio.file_path)

    # Combine diarization and transcription results
    speaker_segments = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        start_time = segment.start
        end_time = segment.end

        # Extract the corresponding text from the transcription
        segment_text = ""
        for item in transcription_result["segments"]:
            if item["start"] >= start_time and item["end"] <= end_time:
                segment_text += item["text"] + " "

        speaker_segments.append({
            "speaker": speaker,
            "start_time": start_time,
            "end_time": end_time,
            "text": segment_text.strip()
        })

    # Save the speaker-segmented transcriptions to the database
    return transcription_crud.create_transcription(
        db, content=speaker_segments, audio_id=audio_id
    )
