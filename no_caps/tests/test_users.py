# test_users.py
import pytest
from db.models.user import User  # Import the SQLAlchemy model, not the schema


def test_create_user(client):
    """Test creating a new user via the API endpoint."""
    test_user = {"email": "test@example.com", "password": "password123"}

    # Create a new user
    response = client.post("/users/", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert "id" in data

    # Test duplicate email
    response = client.post("/users/", json=test_user)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_list_users(client):
    """Test listing users via the API endpoint."""
    # Create test users
    test_users = [
        {"email": f"user{i}@example.com", "password": "password123"} for i in range(3)
    ]

    for user in test_users:
        client.post("/users/", json=user)

    # Test default pagination
    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == 3
    assert data["total"] == 3

    # Test custom pagination
    response = client.get("/users/?skip=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


def test_get_user(client):
    """Test retrieving a user by ID via the API endpoint."""
    # Create a test user
    test_user = {"email": "get_test@example.com", "password": "password123"}
    create_response = client.post("/users/", json=test_user)
    user_id = create_response.json()["id"]

    # Test getting the user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["id"] == user_id

    # Test getting non-existent user
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_update_user(client):
    """Test updating a user via the API endpoint."""
    # Create a test user
    test_user = {"email": "update_test@example.com", "password": "password123"}
    create_response = client.post("/users/", json=test_user)
    user_id = create_response.json()["id"]

    # Test full update
    update_data = {
        "email": "updated@example.com",
        "password": "newpassword123",
        "is_active": False,
    }
    response = client.put(f"/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == update_data["email"]
    assert data["is_active"] == update_data["is_active"]


def test_update_user_invalid_id(client):
    """Test updating a non-existent user."""
    update_data = {"email": "invalid@example.com"}
    response = client.put("/users/999", json=update_data)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_update_user_duplicate_email(client):
    """Test updating a user with an email that already exists."""
    # Create two users
    users = [
        {"email": "user1@example.com", "password": "password123"},
        {"email": "user2@example.com", "password": "password123"},
    ]

    created_users = []
    for user in users:
        response = client.post("/users/", json=user)
        created_users.append(response.json())

    # Try to update second user with first user's email
    update_data = {"email": users[0]["email"]}
    response = client.put(f"/users/{created_users[1]['id']}", json=update_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]
