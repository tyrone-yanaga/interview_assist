import pytest
from unittest import mock
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from db.models.transcription import TranscriptionStatus
from db.models.user import User
from db.models.audio import Audio
from db.models.transcription import Transcription
from core.config import settings
from core.auth import create_access_token


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = mock.MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_audio(mock_user):
    """Create a mock audio file record."""
    audio = mock.MagicMock(spec=Audio)
    audio.id = 1
    audio.filename = "test_audio.mp3"
    audio.file_path = "/path/to/test_audio.mp3"
    audio.user_id = mock_user.id
    return audio


@pytest.fixture
def mock_transcription(mock_audio):
    """Create a mock pending transcription."""
    transcription = mock.MagicMock(spec=Transcription)
    transcription.id = 1
    transcription.audio_id = mock_audio.id
    transcription.status = TranscriptionStatus.PENDING
    transcription.created_at = datetime.now()
    transcription.language = "en"
    return transcription


@pytest.fixture
def mock_completed_transcription(mock_audio):
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
def auth_headers(mock_user):
    """Create valid authentication headers."""
    access_token = create_access_token(
        data={"sub": mock_user.email}, expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


def setup_auth_mocks(monkeypatch, mock_user):
    """Set up common authentication mocks."""
    # Mock the user lookup to return our mock user
    monkeypatch.setattr(
        "db.crud.user.get_user_by_email",
        lambda db, email: mock_user if email == mock_user.email else None,
    )

    # Override the dependency
    async def override_get_current_user():
        return mock_user

    monkeypatch.setattr(
        "api.v1.endpoints.transcription.get_current_user", override_get_current_user
    )


def test_create_transcription(
    auth_client, monkeypatch, mock_user, mock_audio, auth_headers
):
    """Test creating a new transcription."""
    # Set up authentication mocks
    setup_auth_mocks(monkeypatch, mock_user)

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
        f"{settings.API_V1_STR}/transcriptions/transcribe/1", headers=auth_headers
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["transcription_id"] == 1
    assert data["status"] == "pending"


def test_get_transcription_completed(
    client, monkeypatch, mock_user, mock_completed_transcription, auth_headers
):
    """Test getting a completed transcription."""
    # Set up authentication mocks
    setup_auth_mocks(monkeypatch, mock_user)

    # Mock transcription retrieval
    monkeypatch.setattr(
        "db.crud.transcription.TranscriptionCRUD.get_transcription",
        lambda *args, **kwargs: mock_completed_transcription,
    )

    # Mock access permission
    monkeypatch.setattr(
        "services.transcription_service.TranscriptionService.has_access_to_transcription",
        lambda *args, **kwargs: True,
    )

    # Make request with headers
    response = client.get(
        f"{settings.API_V1_STR}/transcriptions/transcription/2", headers=auth_headers
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mock_completed_transcription.id
    assert data["status"] == "completed"
    assert "content" in data
    assert data["content"]["text"] == "This is a test transcription."
    assert data["word_count"] == 5
    assert data["confidence_score"] == 0.95


def test_update_transcription(
    client, monkeypatch, mock_user, mock_transcription, auth_headers
):
    """Test updating a transcription."""
    # Set up authentication mocks
    setup_auth_mocks(monkeypatch, mock_user)

    # Mock access permission
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

    # Make request with headers
    update_data = {
        "content": {
            "text": "Updated transcription text.",
            "segments": [
                {"start": 0.0, "end": 3.0, "text": "Updated transcription text."}
            ],
        }
    }

    response = client.put(
        f"{settings.API_V1_STR}/transcriptions/transcription/1",
        json=update_data,
        headers=auth_headers,
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "completed"


def test_get_transcription_not_found(client, monkeypatch, mock_user, auth_headers):
    """Test getting a non-existent transcription."""
    # Set up authentication mocks
    setup_auth_mocks(monkeypatch, mock_user)

    # Mock transcription retrieval to return None
    monkeypatch.setattr(
        "db.crud.transcription.TranscriptionCRUD.get_transcription",
        lambda *args, **kwargs: None,
    )

    # Make request with headers
    response = client.get(
        f"{settings.API_V1_STR}/transcriptions/transcription/999", headers=auth_headers
    )

    # Check response
    assert response.status_code == 404
    assert "Transcription not found" in response.text
