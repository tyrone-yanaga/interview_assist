# tests/test_transcription.py
import pytest
import json
from unittest import mock
from datetime import datetime
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
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
        audio.duration = 120
        audio.user_id = mock_user.id
        audio.detected_language = "en"
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

    @pytest.fixture
    def mock_failed_transcription(self, mock_audio):
        """Create a mock failed transcription."""
        transcription = mock.MagicMock(spec=Transcription)
        transcription.id = 3
        transcription.audio_id = mock_audio.id
        transcription.status = TranscriptionStatus.FAILED
        transcription.created_at = datetime.now()
        transcription.language = "en"
        transcription.error_message = "Test error message"
        return transcription

    def test_create_transcription(self, auth_client, monkeypatch, mock_user, mock_audio):
        """Test creating a new transcription."""
        # Create a mock JWT token
        token = "test_token"

        # Mock the JWT verification to always return your mock_user
        def mock_verify_token(*args, **kwargs):
            return {"sub": str(mock_user.id)}

        monkeypatch.setattr(
            "core.auth.verify_token",
            mock_verify_token
        )
        # Add the Authorization header
        headers = {"Authorization": f"Bearer {token}"}

        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock get_audio_or_404
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_audio_or_404",
            lambda *args, **kwargs: mock_audio,
        )

        # Mock create_transcription_job
        mock_transcription = mock.MagicMock()
        mock_transcription.id = 1
        mock_transcription.status = TranscriptionStatus.PENDING

        async def mock_create_job(*args, **kwargs):
            return mock_transcription

        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.create_transcription_job",
            mock_create_job,
        )

        # Mock process_transcription
        async def mock_process(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.process_transcription",
            mock_process,
        )

        # Mock BackgroundTasks.add_task to do nothing
        monkeypatch.setattr(
            "fastapi.BackgroundTasks.add_task", lambda self, func, *args, **kwargs: None
        )

        # Make request
        response = auth_client.post(
            f"{settings.API_V1_STR}/transcriptions/transcribe/1",
            headers=headers)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "transcription_id" in data
        assert data["transcription_id"] == 1
        assert data["status"] == "pending"
        assert data["message"] == "Transcription job created"

    def test_get_transcription_status_pending(
        self, client, monkeypatch, mock_user, mock_transcription
    ):
        """Test getting a pending transcription."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock get_transcription
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            lambda *args, **kwargs: mock_transcription,
        )

        # Mock has_access_to_transcription
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: True,
        )

        # Make request
        response = client.get(f"{settings.API_V1_STR}/transcriptions/transcription/1")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_transcription.id
        assert data["status"] == "pending"
        assert "content" not in data
        assert "error" not in data

    def test_get_transcription_status_completed(
        self, client, monkeypatch, mock_user, mock_completed_transcription
    ):
        """Test getting a completed transcription."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock get_transcription
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            lambda *args, **kwargs: mock_completed_transcription,
        )

        # Mock has_access_to_transcription
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: True,
        )

        # Make request
        response = client.get(f"{settings.API_V1_STR}/transcriptions/transcription/2")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_completed_transcription.id
        assert data["status"] == "completed"
        assert "content" in data
        assert data["content"]["text"] == "This is a test transcription."
        assert data["word_count"] == 5
        assert data["confidence_score"] == 0.95

    def test_get_transcription_status_failed(
        self, client, monkeypatch, mock_user, mock_failed_transcription
    ):
        """Test getting a failed transcription."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock get_transcription
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            lambda *args, **kwargs: mock_failed_transcription,
        )

        # Mock has_access_to_transcription
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: True,
        )

        # Make request
        response = client.get(f"{settings.API_V1_STR}/transcriptions/transcription/3")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_failed_transcription.id
        assert data["status"] == "failed"
        assert "error" in data
        assert data["error"] == "Test error message"

    def test_get_transcription_not_found(self, client, monkeypatch, mock_user):
        """Test getting a non-existent transcription."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock get_transcription to return None
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            lambda *args, **kwargs: None,
        )

        # Make request
        response = client.get(f"{settings.API_V1_STR}/transcriptions/transcription/999")

        # Check response
        assert response.status_code == 404
        assert "Transcription not found" in response.text

    def test_get_transcription_unauthorized(
        self, client, monkeypatch, mock_user, mock_transcription
    ):
        """Test getting a transcription without access."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock get_transcription
        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.get_transcription",
            lambda *args, **kwargs: mock_transcription,
        )

        # Mock has_access_to_transcription to return False
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: False,
        )

        # Make request
        response = client.get(f"{settings.API_V1_STR}/transcriptions/transcription/1")

        # Check response
        assert response.status_code == 403
        assert "Not authorized" in response.text

    def test_update_transcription(
        self, client, monkeypatch, mock_user, mock_transcription
    ):
        """Test updating a transcription."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock has_access_to_transcription
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: True,
        )

        # Mock update_transcription_content
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

    def test_update_transcription_unauthorized(self, client, monkeypatch, mock_user):
        """Test updating a transcription without access."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock has_access_to_transcription to return False
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: False,
        )

        # Make request
        update_data = {"content": {"text": "Updated text"}}
        response = client.put(
            f"{settings.API_V1_STR}/transcriptions/transcription/1", json=update_data
        )

        # Check response
        assert response.status_code == 403
        assert "Not authorized" in response.text

    def test_update_transcription_not_found(self, client, monkeypatch, mock_user):
        """Test updating a non-existent transcription."""
        # Mock authentication
        monkeypatch.setattr(
            "api.v1.endpoints.transcription.get_current_user",
            lambda *args, **kwargs: mock_user,
        )

        # Mock has_access_to_transcription
        monkeypatch.setattr(
            "services.transcription_service.TranscriptionService.has_access_to_transcription",
            lambda *args, **kwargs: True,
        )

        # Mock update_transcription_content to return None
        async def mock_update(*args, **kwargs):
            return None

        monkeypatch.setattr(
            "db.crud.transcription.TranscriptionCRUD.update_transcription_content",
            mock_update,
        )

        # Make request
        update_data = {"content": {"text": "Updated text"}}
        response = client.put(
            f"{settings.API_V1_STR}/transcriptions/transcription/999", json=update_data
        )

        # Check response
        assert response.status_code == 404
        assert "Transcription not found" in response.text
