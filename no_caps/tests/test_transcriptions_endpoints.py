# tests/test_transcription.py
import pytest
from unittest import mock
from datetime import datetime
from db.models.transcription import TranscriptionStatus
from db.models.user import User
from db.models.audio import Audio
from db.models.transcription import Transcription
from core.config import settings


class TestTranscriptionEndpoints:
    """Integration tests for transcription endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
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
        audio.user_id = mock_user.id
        return audio

    @pytest.fixture
    def mock_transcription(self, mock_audio):
        """Create a mock pending transcription."""
        transcription = mock.MagicMock(spec=Transcription)
        transcription.id = 1
        transcription.audio_id = mock_audio.id
        transcription.status = TranscriptionStatus.PENDING
        transcription.created_at = datetime.now()
        transcription.language = "en"
        return transcription

    @pytest.fixture
    def mock_completed_transcription(self, mock_audio):
        """Create a mock completed transcription."""
        transcription = mock.MagicMock(spec=Transcription)
        transcription.id = 2
        transcription.audio_id = mock_audio.id
        transcription.status = TranscriptionStatus.COMPLETED
        transcription.created_at = datetime.now()
        transcription.completed_at = datetime.now()
        transcription.language = "en"
        transcription.content = {
            "text": "This is a test transcription.",
            "segments": [{"start": 0.0, "end": 2.5, "text": "This is a test"}],
        }
        transcription.word_count = 5
        transcription.confidence_score = 0.95
        return transcription

    def test_create_transcription(
        self, auth_client, monkeypatch, mock_user, mock_audio
    ):
        """Test creating a new transcription."""
        # Create a real-looking token
        from datetime import timedelta
        from core.auth import create_access_token, get_current_user

        # Set up the mock user with email
        mock_user.email = "test@example.com"

        # Create a real token
        access_token = create_access_token(
            data={"sub": mock_user.email}, expires_delta=timedelta(minutes=30)
        )

        # Add Authorization headers with the real token
        headers = {"Authorization": f"Bearer {access_token}"}

        # Mock the get_user_by_email function to return our mock user
        monkeypatch.setattr(
            "db.crud.user.get_user_by_email",
            lambda db, email: mock_user if email == mock_user.email else None,
        )

        # The core issue - monkeypatch the fastapi dependency injection directly
        # This bypasses the entire authentication flow and just returns our mock user
        async def override_get_current_user():
            return mock_user

        # Apply the monkeypatch directly to the dependency
        import importlib

        transcription_module = importlib.import_module("api.v1.endpoints.transcription")
        original_dependencies = getattr(transcription_module, "__dict__", {}).copy()

        # Here's the key - we're directly patching the dependency lookup
        for key, value in original_dependencies.items():
            if (
                hasattr(value, "dependencies")
                and get_current_user in value.dependencies
            ):
                # Found the dependency on get_current_user, replace it with our override
                for i, dep in enumerate(value.dependencies):
                    if dep == get_current_user:
                        value.dependencies[i] = override_get_current_user

        # Mock get_audio_or_404
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_audio_or_404",
            lambda *args, **kwargs: mock_audio,
        )

        # Mock transcription creation
        mock_transcription = mock.MagicMock()
        mock_transcription.id = 1
        mock_transcription.status = TranscriptionStatus.PENDING

        async def mock_create_job(*args, **kwargs):
            return mock_transcription

        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.create_transcription_job",
            mock_create_job,
        )

        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.process_transcription",
            lambda *args, **kwargs: None,
        )

        monkeypatch.setattr(
            "fastapi.BackgroundTasks.add_task", lambda self, func, *args, **kwargs: None
        )

        # Make request
        response = auth_client.post(
            f"{settings.API_V1_STR}/transcriptions/transcribe/1", headers=headers
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["transcription_id"] == 1
        assert data["status"] == "pending"

    def test_get_transcription_completed(
        self, client, monkeypatch, mock_completed_transcription, mock_user
    ):
        """Test getting a completed transcription."""
        # Add authorization header
        headers = {"Authorization": "Bearer test_token"}

        # Patch token validation
        def mock_decode(*args, **kwargs):
            return {"sub": str(mock_user.id)}

        monkeypatch.setattr("jose.jwt.decode", mock_decode)

        # Mock authentication function
        async def mock_current_user(*args, **kwargs):
            return mock_user

        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user", mock_current_user
        )
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            lambda *args, **kwargs: mock_completed_transcription,
        )
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: True,
        )

        # Make request with headers
        response = client.get(
            f"{settings.API_V1_STR}/transcriptions/transcription/2", headers=headers
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_completed_transcription.id
        assert data["status"] == "completed"
        assert data["content"]["text"] == "This is a test transcription."

    def test_update_transcription(
        self, client, monkeypatch, mock_user, mock_transcription
    ):
        """Test updating a transcription."""
        # Mock authentication and authorization
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: True,
        )

        # Mock update operation
        updated_transcription = mock.MagicMock()
        updated_transcription.id = 1
        updated_transcription.status = TranscriptionStatus.COMPLETED
        updated_transcription.created_at = datetime.now()

        async def mock_update(*args, **kwargs):
            return updated_transcription

        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_content",
            mock_update,
        )

        # Make request
        update_data = {
            "content": {
                "text": "Updated transcription text.",
                "segments": [
                    {"start": 0.0, "end": 3.0, "text": "Updated transcription text."}
                ],
            }
        }
        response = client.put(
            f"{settings.API_V1_STR}/transcriptions/transcription/1", json=update_data
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["status"] == "completed"

    def test_get_transcription_not_found(self, client, monkeypatch, mock_user):
        """Test getting a non-existent transcription."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            lambda *args, **kwargs: None,
        )

        # Make request with headers
        response = client.get(
            f"{settings.API_V1_STR}/transcriptions/transcription/999", headers=headers
        )

        # Check response
        assert response.status_code == 404
        assert "Transcription not found" in response.text
