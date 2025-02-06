from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import boto3
import uuid
import os
from celery import Celery
import whisper
from pyannote.audio import Pipeline
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Audio Processing API")

# Configure Celery
celery = Celery("tasks", broker="redis://localhost:6379/0")

# Configure AWS S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


# Database Models
class AudioFile(BaseModel):
    id: str
    filename: str
    s3_url: str
    status: str
    transcript: Optional[str] = None
    diarization: Optional[dict] = None
    created_at: datetime


# Initialize Whisper and Pyannote
whisper_model = whisper.load_model("base")
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization", use_auth_token=os.getenv("HUGGINGFACE_TOKEN")
)


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    try:
        # Generate unique ID for the audio file
        file_id = str(uuid.uuid4())

        # Upload to S3
        s3_path = f"audio/{file_id}/{file.filename}"
        s3_client.upload_fileobj(file.file, BUCKET_NAME, s3_path)

        # Create database entry
        audio_file = AudioFile(
            id=file_id,
            filename=file.filename,
            s3_url=f"s3://{BUCKET_NAME}/{s3_path}",
            status="processing",
            created_at=datetime.utcnow(),
        )

        # Trigger async processing
        process_audio.delay(file_id)

        return JSONResponse(
            {"message": "Audio file uploaded successfully", "file_id": file_id}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@celery.task
def process_audio(file_id: str):
    try:
        # Download file from S3
        local_path = f"/tmp/{file_id}.wav"
        s3_client.download_file(BUCKET_NAME, f"audio/{file_id}", local_path)

        # Transcribe audio
        result = whisper_model.transcribe(local_path)
        transcript = result["text"]

        # Perform diarization
        diarization = diarization_pipeline(local_path)

        # Convert diarization to serializable format
        speakers = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end
                })

        # Update database entry
        # Note: In a real implementation, you'd want to use your ORM of choice
        # to update the database

        # Clean up local file
        os.remove(local_path)

        return {
            "file_id": file_id,
            "status": "completed",
            "transcript": transcript,
            "diarization": speakers,
        }

    except Exception as e:
        # Update database with error status
        print(f"Error processing audio {file_id}: {str(e)}")
        return {"file_id": file_id, "status": "error", "error": str(e)}


@app.get("/status/{file_id}")
async def get_status(file_id: str):
    try:
        # Retrieve status from database
        # This is a placeholder - implement actual database query
        return JSONResponse(
            {
                "file_id": file_id,
                "status": "processing",  # Or completed/error based on DB
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {e}")


@app.get("/result/{file_id}")
async def get_result(file_id: str):
    try:
        # Retrieve results from database
        # This is a placeholder - implement actual database query
        return JSONResponse(
            {
                "file_id": file_id,
                "status": "completed",
                "transcript": "Sample transcript",
                "diarization": [],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {e}")


# Configuration and environment settings
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)