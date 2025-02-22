# tests/test_transcriptions.py

# TODO - implement after audio
import logging
import json
from core.config import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_create_transcription(client):
    """Test creating a new transcription via the API endpoint."""
    logger.debug("\n=== Starting test_create_transcription ===")

    # Verify routes are registered
    routes = [f"{route.methods} {route.path}" for route in client.app.routes]
    logger.debug(f"Available routes: {json.dumps(routes, indent=2)}")

    test_user = {"email": "test@example.com", "password": "password123"}
    endpoint = f"{settings.API_V1_STR}/users/"

    logger.debug(f"Making POST request to: {endpoint}")
    logger.debug(f"Request body: {json.dumps(test_user, indent=2)}")

    response = client.post(endpoint, json=test_user)
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response body: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["email"] == test_user["email"]


def test_get_transcription(client):
    """Test retrieving a transcription by ID via the API endpoint."""
    # Create test transcription
    test_user = {"email": "get_test@example.com", "password": "password123"}
    create_response = client.post(f"{settings.API_V1_STR}/users/", json=test_user)
    assert create_response.status_code == 200
    transcription_id = create_response.json()["id"]

    # Get transcription
    response = client.get(f"{settings.API_V1_STR}/transcriptions/{transcription_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_transcription["email"]


def test_update_transcription(client):
    """Test updating a transcription via the API endpoint."""
    # Create test transcription
    test_user = {"email": "update_test@example.com", "password": "password123"}
    create_response = client.post(f"{settings.API_V1_STR}/users/", json=test_user)
    assert create_response.status_code == 200
    transcription_id = create_response.json()["id"]

    # Update transcription
    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123",
        "is_active": False,
    }
    response = client.put(f"{settings.API_V1_STR}/transcriptions/{transcription_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
