# tests/test_audio_endpoints.py
import pytest
from fastapi import UploadFile
from io import BytesIO
import os
from unittest.mock import patch, MagicMock
from core.config import settings

# Test data
TEST_AUDIO_FILENAME = "test_audio.mp3"
TEST_AUDIO_CONTENT = b"mock audio content"
TEST_USER_ID = 1
TEST_AUDIO_ID = 1
TEST_DURATION = 120  # 2 minutes in seconds

# API endpoint prefix
API_AUDIO_PREFIX = f"{settings.API_V1_STR}/audio"


@pytest.fixture
def mock_audio_file():
    """Create a mock audio file for testing"""
    file = UploadFile(filename=TEST_AUDIO_FILENAME,
                      file=BytesIO(TEST_AUDIO_CONTENT))
    # Set content type after creation
    return {"file": file}


@pytest.fixture
def mock_audio_record():
    """Create a mock audio database record"""
    return {
        "id": TEST_AUDIO_ID,
        "filename": TEST_AUDIO_FILENAME,
        "file_path": f"/uploads/{TEST_AUDIO_FILENAME}",
        "duration": TEST_DURATION,
        "user_id": TEST_USER_ID,
        "created_at": "2025-02-21T10:00:00",
    }


@pytest.mark.asyncio
async def test_upload_audio_success(client, test_db, mock_audio_file):
    """Test successful audio file upload"""
    # Mock the file saving and audio processing functions
    with patch("utils.file_handling.save_upload_file") as mock_save, patch(
        "utils.audio_processing.get_audio_duration"
    ) as mock_duration:

        mock_save.return_value = f"/uploads/{TEST_AUDIO_FILENAME}"
        mock_duration.return_value = TEST_DURATION

        response = await client.post(
            f"{API_AUDIO_PREFIX}/upload/", files=mock_audio_file
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == TEST_AUDIO_FILENAME
        assert data["duration"] == TEST_DURATION
        assert data["user_id"] == TEST_USER_ID


@pytest.mark.asyncio
async def test_upload_audio_invalid_file_type(client, test_db, mock_audio_file):
    """Test upload with invalid file type"""
    # Modify the content type of the mock file
    mock_audio_file["file"].content_type = "text/plain"

    response = await client.post(f"{API_AUDIO_PREFIX}/upload/", files=mock_audio_file)

    assert response.status_code == 400
    assert "File must be an audio file" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_audio_files_success(client, test_db, mock_audio_record):
    """Test getting user's audio files"""
    # Insert a mock audio record
    with patch("db.crud.audio.get_user_audio_files") as mock_get:
        mock_get.return_value = [mock_audio_record]

        response = await client.get(f"{API_AUDIO_PREFIX}/{TEST_USER_ID}/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"] == TEST_AUDIO_FILENAME
        assert data[0]["user_id"] == TEST_USER_ID


@pytest.mark.asyncio
async def test_get_user_audio_files_empty(client, test_db):
    """Test getting audio files for user with no files"""
    response = await client.get(f"{API_AUDIO_PREFIX}/{TEST_USER_ID}/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_audio_success(client, test_db, mock_audio_record):
    """Test successful audio file deletion"""
    # First insert a mock audio record
    with patch("db.crud.audio.get_audio_or_404") as mock_get, patch(
        "db.crud.audio.delete_audio"
    ) as mock_delete:

        mock_get.return_value = mock_audio_record
        mock_delete.return_value = True

        response = await client.delete(f"{API_AUDIO_PREFIX}/{TEST_AUDIO_ID}")

        assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_audio_not_found(client, test_db):
    """Test deleting non-existent audio file"""
    non_existent_id = 999
    response = await client.delete(f"{API_AUDIO_PREFIX}/{non_existent_id}")

    assert response.status_code == 404
    assert f"Audio with ID {non_existent_id} not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_audio_unauthorized(client, test_db, mock_audio_record):
    """Test deleting audio file belonging to another user"""
    unauthorized_user_id = 2

    with patch("db.crud.audio.get_audio_or_404") as mock_get:
        mock_get.return_value = mock_audio_record

        # Simulate request with different user_id
        response = await client.delete(
            f"{API_AUDIO_PREFIX}/{TEST_AUDIO_ID}",
            headers={"X-User-ID": str(unauthorized_user_id)},
        )

        assert response.status_code == 403
        assert "Not authorized to delete this audio file" in response.json()["detail"]
