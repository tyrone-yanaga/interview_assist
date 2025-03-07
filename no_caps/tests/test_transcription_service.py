# tests/test_transcription_service.py
import pytest
from unittest import mock
from datetime import datetime
from sqlalchemy.orm import Session
from services.transcription_service import TranscriptionService
from db.models.transcription import Transcription, TranscriptionStatus
from db.models.audio import Audio
from db.models.user import User


class TestTranscriptionService:
    """Core tests for TranscriptionService."""

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
        return user

    @pytest.fixture
    def mock_audio(self, mock_user):
        """Create a mock audio file record."""
        audio = mock.MagicMock(spec=Audio)
        audio.id = 1
        audio.file_path = "/path/to/test_audio.mp3"
        audio.user_id = mock_user.id
        return audio

    @pytest.fixture
    def mock_transcription(self, mock_audio):
        """Create a mock transcription."""
        transcription = mock.MagicMock(spec=Transcription)
        transcription.id = 1
        transcription.audio_id = mock_audio.id
        transcription.status = TranscriptionStatus.PENDING
        transcription.audio_file = mock_audio
        return transcription

    @pytest.mark.asyncio
    async def test_create_transcription_job(
        self, transcription_service, mock_db, mock_audio, monkeypatch
    ):
        """Test creating a transcription job."""
        # Arrange
        mock_transcription = mock.MagicMock(spec=Transcription)

        async def mock_create(*args, **kwargs):
            return mock_transcription

        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.create_transcription", mock_create
        )

        # Act
        result = await transcription_service.create_transcription_job(
            db=mock_db, audio_id=mock_audio.id, language="en"
        )

        # Assert
        assert result == mock_transcription

    @pytest.mark.asyncio
    async def test_process_transcription_success(
        self, transcription_service, mock_db, mock_transcription, monkeypatch
    ):
        """Test successful transcription processing."""
        # Arrange
        audio_path = "/path/to/test_audio.mp3"

        monkeypatch.setattr("os.path.exists", lambda path: True)

        async def mock_get_transcription(*args, **kwargs):
            return mock_transcription

        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            mock_get_transcription,
        )

        async def mock_update_status(*args, **kwargs):
            return None

        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_status",
            mock_update_status,
        )

        # Mock the internal transcription process
        class MockTranscriber:
            async def transcribe(self, *args, **kwargs):
                return {
                    "text": "This is a test transcription.",
                    "segments": [
                        {
                            "start": 0.0,
                            "end": 2.5,
                            "text": "This is a test transcription.",
                        }
                    ],
                }

        transcription_service.transcriber = MockTranscriber()

        async def mock_update_content(*args, **kwargs):
            return mock_transcription

        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_content",
            mock_update_content,
        )

        # Act - this should now use our mocked transcriber
        await transcription_service.process_transcription(
            db=mock_db, transcription_id=mock_transcription.id, audio_path=audio_path
        )

        # Success if no exceptions

    def test_has_access_to_transcription(
        self, transcription_service, mock_db, mock_transcription, mock_user, mock_audio
    ):
        """Test permission verification for transcription access."""

        # Set up the mock for get_audio_or_404
        def mock_get_audio(db, audio_id, user_id):
            if user_id == mock_audio.user_id:
                return mock_audio
            raise Exception("Not authorized")

        # Store original and replace
        original_func = getattr(transcription_service, "get_audio_or_404", None)
        transcription_service.get_audio_or_404 = mock_get_audio

        try:
            # Test authorized user
            result = transcription_service.has_access_to_transcription(
                db=mock_db, transcription=mock_transcription, user_id=mock_user.id
            )
            assert result is True

            # Test unauthorized user
            result = transcription_service.has_access_to_transcription(
                db=mock_db, transcription=mock_transcription, user_id=999
            )
            assert result is False
        finally:
            # Restore original if it existed
            if original_func:
                transcription_service.get_audio_or_404 = original_func
