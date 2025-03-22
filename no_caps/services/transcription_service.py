from typing import Optional, Tuple, List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from whisper import Whisper
from pyannote.audio import Pipeline
from db.crud.transcription import TranscriptionCRUD
from db.crud.audio import get_audio_or_404
from db.models.transcription import Transcription, TranscriptionStatus
from core.config import settings
from core.logging import logger


class TranscriptionService:
    """Business logic for transcription operations.

    Responsibilities:
    - Implement transcription business logic
    - Handle the transcription process
    - Coordinate between different components
    - Handle error cases and recovery
    """

    def __init__(self):
        # Load Whisper model for transcription
        self.whisper_model = Whisper.load_model(settings.WHISPER_MODEL_SIZE)

        # Load pyannote.audio pipeline for diarization
        self.diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token="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")

    async def create_transcription_job(
        self,
        db: Session,
        audio_id: int,
        language: str = "en"
    ) -> Transcription:
        """Create a new transcription job."""
        try:
            return TranscriptionCRUD.create_transcription(
                db=db,
                audio_id=audio_id,
                language=language
            )
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                # If a transcription already exists, return it
                return TranscriptionCRUD.get_transcription(db, audio_id)
            raise

    async def process_transcription(
        self,
        db: Session,
        transcription_id: int,
        audio_path: str
    ) -> Tuple[bool, Optional[str]]:
        """Process the transcription job."""
        existing_transcription = TranscriptionCRUD.get_transcription_by_id(
            db, transcription_id)

        if existing_transcription and existing_transcription.status == TranscriptionStatus.FAILED:
            # Update the existing record to retrying
            TranscriptionCRUD.update_transcription_status(
                db,
                transcription_id,
                TranscriptionStatus.RETRYING
            )
        else:
            # Update status to in progress
            TranscriptionCRUD.update_transcription_status(
                db,
                transcription_id,
                TranscriptionStatus.IN_PROGRESS
            )

        try:
            # Perform diarization
            diarization = self.diarization_pipeline(audio_path)

            # Perform transcription
            transcription_result = self.whisper_model.transcribe(audio_path)

            # Combine diarization and transcription results
            speaker_segments = self._combine_diarization_and_transcription(
                diarization, transcription_result
            )

            # Calculate metrics
            word_count = sum(len(
                segment["text"].split()) for segment in speaker_segments)
            confidence_score = self._calculate_confidence(transcription_result)
            # TODO talk time, information summary, extract todos

            # Update with results
            TranscriptionCRUD.update_transcription_content(
                db,
                transcription_id,
                content=speaker_segments,
                word_count=word_count,
                confidence_score=confidence_score
            )

            return True, None

        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            logger.error(error_msg)

            # Update status to failed
            TranscriptionCRUD.update_transcription_status(
                db,
                transcription_id,
                TranscriptionStatus.FAILED,
                error_msg
            )

            return False, error_msg

    def _combine_diarization_and_transcription(
        self,
        diarization,
        transcription_result: dict
    ) -> List[Dict[str, str]]:
        """Combine diarization and transcription results
         into speaker-segmented transcriptions."""
        speaker_segments = []

        # Iterate over diarization segments
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

        return speaker_segments

    def _calculate_confidence(self, result: dict) -> float:
        """Calculate overall confidence score."""
        if "segments" in result:
            confidences = [seg.get("confidence", 0) for seg in result[
                "segments"]]
            return sum(confidences) / len(confidences) if confidences else 0
        return 0

    def has_access_to_transcription(
            self,
            db: Session,
            transcription: Transcription,
            user_id: int) -> bool:
        """does the user have access to this transcription"""

        try:
            audio = get_audio_or_404(
                db,
                audio_id=transcription.audio_id,
                user_id=user_id)
            if audio: 
                return True
        except HTTPException as e:
            if e.status_code == 404:
                # Handle the 404 error specifically
                return False
            else:
                # Re-raise any other HTTP exceptions
                raise e
        return False