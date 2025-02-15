from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session
import whisper
from pyannote.audio import Pipeline
from db.crud.transcription import TranscriptionCRUD
from db.crud.audio import get_audio_or_404
from db.models.transcription import TranscriptionModel, TranscriptionStatus
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
        self.whisper_model = whisper.load_model(settings.WHISPER_MODEL_SIZE)

        # Load pyannote.audio pipeline for diarization
        self.diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization")

    async def create_transcription_job(
        self,
        db: Session,
        audio_id: int,
        language: str = "en"
    ) -> TranscriptionModel:
        """Create a new transcription job."""
        return TranscriptionCRUD.create_transcription(
            db=db,
            audio_id=audio_id,
            language=language
        )

    async def process_transcription(
        self,
        db: Session,
        transcription_id: int,
        audio_path: str
    ) -> Tuple[bool, Optional[str]]:
        """Process the transcription job."""
        try:
            # Update status to in progress
            TranscriptionCRUD.update_transcription_status(
                db,
                transcription_id,
                TranscriptionStatus.IN_PROGRESS
            )

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
            transcription: TranscriptionModel,
            user_id: int) -> bool:
        """does the user have access to this transcription"""

        audio = get_audio_or_404(
            db,
            audio_id=transcription.audio_id,
            user_id=user_id)
        if audio:
            return True
        else:
            return False
