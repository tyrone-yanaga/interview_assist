# tests/test_audio.py
import io
import pytest
import json
from unittest import mock
from fastapi import UploadFile
from core.config import settings


def test_audio_upload_success(client, monkeypatch):
    """Test successful audio file upload."""

    # Mock file saving to avoid actual file operations during testing
    async def mock_save_upload_file(file):
        return "/mocked/path/to/audio.mp3"

    # Mock audio duration calculation
    def mock_get_audio_duration(file_path):
        return 120  # 2 minutes duration

    # Apply our mocks
    monkeypatch.setattr(
        "services.audio_service.save_upload_file", mock_save_upload_file
    )
    monkeypatch.setattr(
        "services.audio_service.get_audio_duration", mock_get_audio_duration
    )
    monkeypatch.setattr(
        "db.crud.audio.create_audio",
        lambda db, filename, file_path, duration, user_id: {
            "id": 1,
            "filename": filename,
            "file_path": file_path,
            "duration": duration,
            "user_id": user_id,
            "created_at": "2025-02-24T00:00:00",
        },
    )

    # Create test file data
    test_file_name = "test_audio.mp3"
    test_file_content = b"mock audio file content"

    # Create a file-like object for the test
    test_file = io.BytesIO(test_file_content)

    # Make the file upload request
    files = {"file": (test_file_name, test_file, "audio/mpeg")}

    response = client.post(f"{settings.API_V1_STR}/audio/upload/", files=files)

    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == test_file_name
    assert data["user_id"] == 1  # Your service hardcodes user_id to 1
    assert data["duration"] == 120  # Our mocked duration


def test_audio_upload_failure(client, monkeypatch):
    """Test audio upload failure with invalid file type."""

    # Mock file saving to avoid actual file operations during testing
    async def mock_save_upload_file(file):
        return "/mocked/path/to/file.txt"

    monkeypatch.setattr(
        "services.audio_service.save_upload_file", mock_save_upload_file
    )

    # Create test file data with an invalid format
    test_file_name = "test_document.txt"
    test_file_content = b"This is a text file, not an audio file"

    # Create a file-like object for the test
    test_file = io.BytesIO(test_file_content)

    # Make the file upload request with a non-audio file
    files = {"file": (test_file_name, test_file, "text/plain")}

    response = client.post(f"{settings.API_V1_STR}/audio/upload/", files=files)

    # Assert the response
    assert response.status_code == 400
    assert "File must be an audio file" in response.text


def test_get_audio_uploads_success(client, monkeypatch):
    """Test retrieving audio files for a user."""
    # Mock the get_user_audio_files function
    test_audio_files = [
        {
            "id": 1,
            "filename": "audio1.mp3",
            "file_path": "/path/to/audio1.mp3",
            "duration": 60,
            "user_id": 1,
            "created_at": "2025-02-24T00:00:00",
        },
        {
            "id": 2,
            "filename": "audio2.mp3",
            "file_path": "/path/to/audio2.mp3",
            "duration": 120,
            "user_id": 1,
            "created_at": "2025-02-24T00:00:00",
        },
    ]

    def mock_get_user_audio_files(db, user_id):
        return test_audio_files

    monkeypatch.setattr("db.crud.audio.get_user_audio_files", mock_get_user_audio_files)

    # Get audio files for user_id=1
    response = client.get(f"{settings.API_V1_STR}/audio/1/")

    # Assert the response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Check that the files match our mock data
    assert data[0]["filename"] == "audio1.mp3"
    assert data[1]["filename"] == "audio2.mp3"


def test_upload_no_file(client):
    """Test audio upload failure when no file is provided."""
    # Make the file upload request without a file
    response = client.post(f"{settings.API_V1_STR}/audio/upload/")

    # Assert the response
    assert response.status_code == 422  # Validation error for missing required field


def test_get_audio_nonexistent_user(client, monkeypatch):
    """Test getting audio files for a user that doesn't exist."""

    # Mock the get_user_audio_files function to return empty list
    def mock_get_user_audio_files(db, user_id):
        if user_id == 999:
            return []
        else:
            return [{"id": 1, "filename": "test.mp3"}]

    monkeypatch.setattr("db.crud.audio.get_user_audio_files", mock_get_user_audio_files)

    # Get audio files for a non-existent user
    response = client.get(f"{settings.API_V1_STR}/audio/999/")

    # Assuming your API returns an empty list for users with no files
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0
