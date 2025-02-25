# tests/test_users.py
import logging
import json
from core.config import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_create_user(client):
    """Test creating a new user via the API endpoint."""
    logger.debug("\n=== Starting test_create_user ===")

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


def test_list_users(client):
    """Test listing users via the API endpoint."""
    test_users = [
        {"email": f"user{i}@example.com", "password": "password123"} for i in range(3)
    ]

    # Create test users with correct endpoint
    endpoint = f"{settings.API_V1_STR}/users/"
    for user in test_users:
        client.post(endpoint, json=user)

    # Test default pagination
    response = client.get(endpoint)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3


def test_get_user(client):
    """Test retrieving a user by ID via the API endpoint."""
    # Create test user
    test_user = {"email": "get_test@example.com", "password": "password123"}
    create_response = client.post(f"{settings.API_V1_STR}/users/", json=test_user)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Get user
    response = client.get(f"{settings.API_V1_STR}/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]


def test_update_user(client):
    """Test updating a user via the API endpoint."""
    # Create test user
    test_user = {"email": "update_test@example.com", "password": "password123"}
    create_response = client.post(f"{settings.API_V1_STR}/users/", json=test_user)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Update user
    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123",
        "is_active": False,
    }
    response = client.put(f"{settings.API_V1_STR}/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
