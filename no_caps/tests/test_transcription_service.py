# tests/test_transcription_service.py
import pytest
import json
from unittest import mock
from datetime import datetime
from sqlalchemy.orm import Session
from services.transcription_service import TranscriptionService
from db.models.transcription import Transcription, TranscriptionStatus
from db.models.audio import Audio
from db.models.user import User


class TestTranscriptionService:
    """Unit tests for TranscriptionService."""

    @pytest.fixture
    def transcription_service(self):
        """Create a TranscriptionService instance for testing."""
        return TranscriptionService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return mock.MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = mock.MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_audio(self, mock_user):
        """Create a mock audio file record."""
        audio = mock.MagicMock(spec=Audio)
        audio.id = 1
        audio.filename = "test_audio.mp3"
        audio.file_path = "/path/to/test_audio.mp3"
        audio.duration = 120
        audio.user_id = mock_user.id
        audio.detected_language = "en"
        audio.transcription = None
        return audio

    @pytest.fixture
    def mock_transcription(self, mock_audio):
        """Create a mock transcription."""
        transcription = mock.MagicMock(spec=Transcription)
        transcription.id = 1
        transcription.audio_id = mock_audio.id
        transcription.status = TranscriptionStatus.PENDING
        transcription.created_at = datetime.now()
        transcription.language = "en"
        transcription.audio_file = mock_audio
        return transcription

    @pytest.mark.asyncio
    async def test_create_transcription_job(
        self, transcription_service, mock_db, mock_audio
    ):
        """Test creating a transcription job."""
        # Arrange
        mock_transcription = mock.MagicMock(spec=Transcription)
        mock_transcription.id = 1
        mock_transcription.status = TranscriptionStatus.PENDING

        # Mock TranscriptionCRUD.create_transcription
        mock_create = mock.AsyncMock(return_value=mock_transcription)
        monkeypatch = mock.patch(
            "db.crud.transcription.TranscriptionCRUD.create_transcription", mock_create
        )
        monkeypatch.start()

        # Act
        result = await transcription_service.create_transcription_job(
            db=mock_db, audio_id=mock_audio.id, language="en"
        )

        # Assert
        mock_create.assert_called_once_with(
            db=mock_db, audio_id=mock_audio.id, language="en"
        )
        assert result == mock_transcription
        assert result.status == TranscriptionStatus.PENDING

        # Cleanup
        monkeypatch.stop()

    @pytest.mark.asyncio
    async def test_process_transcription_success(
        self, transcription_service, mock_db, mock_transcription, monkeypatch
    ):
        """Test successful transcription processing."""
        # Arrange
        audio_path = "/path/to/test_audio.mp3"

        # Mock get_transcription
        get_transcription_mock = mock.MagicMock(return_value=mock_transcription)
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            get_transcription_mock,
        )

        # Mock update_transcription_status
        update_status_mock = mock.AsyncMock()
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_status",
            update_status_mock,
        )

        # Mock the actual transcription process
        mock_result = {
            "text": "This is a test transcription.",
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "This is a test transcription."}
            ],
        }

        # Mock update_transcription_content
        update_content_mock = mock.AsyncMock(return_value=mock_transcription)
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_content",
            update_content_mock,
        )

        # Act
        await transcription_service.process_transcription(
            db=mock_db, transcription_id=mock_transcription.id, audio_path=audio_path
        )

        # Assert
        get_transcription_mock.assert_called_once_with(
            db=mock_db, transcription_id=mock_transcription.id
        )

        update_status_mock.assert_called_with(
            db=mock_db,
            transcription_id=mock_transcription.id,
            status=TranscriptionStatus.IN_PROGRESS,
        )

        # Check that the final update includes the correct data
        update_content_mock.assert_called_once()
        call_args = update_content_mock.call_args[0]
        assert call_args[0] == mock_db
        assert call_args[1] == mock_transcription.id

        # Check that the update data contains the right fields
        update_data = update_content_mock.call_args[0][2]
        assert update_data["content"] == mock_result
        assert update_data["status"] == TranscriptionStatus.COMPLETED
        assert "completed_at" in update_data
        assert "word_count" in update_data
        assert "confidence_score" in update_data

    @pytest.mark.asyncio
    async def test_process_transcription_failure(
        self, transcription_service, mock_db, mock_transcription, monkeypatch
    ):
        """Test failed transcription processing."""
        # Arrange
        audio_path = "/path/to/test_audio.mp3"

        # Mock get_transcription
        get_transcription_mock = mock.MagicMock(return_value=mock_transcription)
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            get_transcription_mock,
        )

        # Mock update_transcription_status
        update_status_mock = mock.AsyncMock()
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_status",
            update_status_mock,
        )

        # Mock the speech_to_text to raise an exception
        error_message = "Test transcription error"
        speech_to_text_mock = mock.AsyncMock(side_effect=Exception(error_message))
        monkeypatch.setattr(
            "services.transcription_service.speech_to_text", speech_to_text_mock
        )

        # Mock update_transcription_status for the failure case
        update_failure_mock = mock.AsyncMock()
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_failure",
            update_failure_mock,
        )

        # Act
        await transcription_service.process_transcription(
            db=mock_db, transcription_id=mock_transcription.id, audio_path=audio_path
        )

        # Assert
        get_transcription_mock.assert_called_once()

        update_status_mock.assert_called_with(
            db=mock_db,
            transcription_id=mock_transcription.id,
            status=TranscriptionStatus.IN_PROGRESS,
        )

        speech_to_text_mock.assert_called_once()

        update_failure_mock.assert_called_once()
        call_args = update_failure_mock.call_args[0]
        assert call_args[0] == mock_db
        assert call_args[1] == mock_transcription.id
        assert error_message in call_args[2]  # Error message should be included

    def test_has_access_to_transcription(
        self, transcription_service, mock_db, mock_transcription, mock_user
    ):
        """Test permission verification for transcription access."""
        # Arrange
        # Mock get_transcription
        get_transcription_mock = mock.MagicMock(return_value=mock_transcription)

        with mock.patch(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            get_transcription_mock,
        ):
            # Case 1: User is the owner of the audio file
            mock_transcription.audio_file.user_id = mock_user.id

            # Act & Assert
            result = transcription_service.has_access_to_transcription(
                db=mock_db, transcription=mock_transcription.id, user_id=mock_user.id
            )
            assert result is True

            # Case 2: User is not the owner
            mock_transcription.audio_file.user_id = 999  # Different user

            # Act & Assert
            result = transcription_service.has_access_to_transcription(
                db=mock_db, transcription=mock_transcription.id, user_id=mock_user.id
            )
            assert result is False
