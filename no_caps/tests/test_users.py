# test_users.py
import pytest
# from httpx import AsyncClient
from db.crud import user as user_crud
# from db.schemas import UserResponse
# from db.models import User


@pytest.mark.asyncio
async def test_create_user(client):
    """
    Test creating a new user.
    """
    # Create a new user
    response = await client.post(
        "/users/", json={"email": "test@example.com",
                         "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # Attempt to create a user with the same email (duplicate email)
    response = await client.post(
        "/users/", json={"email": "test@example.com",
                         "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_list_users(client, test_db):
    """
    Test listing users with pagination.
    """
    # Create multiple users
    user_crud.create_user(test_db,
                          email="user1@example.com",
                          password="password123")
    user_crud.create_user(test_db,
                          email="user2@example.com",
                          password="password123")
    user_crud.create_user(test_db,
                          email="user3@example.com",
                          password="password123")

    # Test listing users with default pagination (skip=0, limit=10)
    response = await client.get("/users/", params={"skip": 0, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3

    # Test listing users with pagination (skip=1, limit=2)
    response = await client.get("/users/", params={"skip": 1, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_get_user(client, test_db):
    """
    Test retrieving a user by ID.
    """
    # Create a user
    user = user_crud.create_user(
        test_db, email="user@example.com", password="password123"
    )

    # Test retrieving the user by ID
    response = await client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["id"] == user.id

    # Test retrieving a non-existent user
    response = await client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_user(client, test_db):
    """
    Test updating a user's information.
    """
    # Create a user
    user = user_crud.create_user(
        test_db, email="user@example.com", password="password123"
    )

    # Test updating the user's email and is_active status
    update_data = {"email": "updated@example.com", "is_active": False}
    response = await client.put(f"/users/{user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    assert data["is_active"] is False

    # Verify the update in the database
    updated_user = user_crud.get_user(test_db, user_id=user.id)
    assert updated_user.email == "updated@example.com"
    assert updated_user.is_active is False

    # Test updating only the password
    update_data = {"password": "newpassword123"}
    response = await client.put(f"/users/{user.id}", json=update_data)
    assert response.status_code == 200

    # Verify the password update in the database
    updated_user = user_crud.get_user(test_db, user_id=user.id)
    assert updated_user.password == "newpassword123"


@pytest.mark.asyncio
async def test_update_user_invalid_id(client):
    """
    Test updating a user with an invalid ID.
    """
    update_data = {"email": "updated@example.com", "is_active": False}
    response = await client.put("/users/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_user_partial_data(client, test_db):
    """
    Test updating a user with partial data (only some fields provided).
    """
    # Create a user
    user = user_crud.create_user(
        test_db, email="user@example.com", password="password123"
    )

    # Update only the email
    update_data = {"email": "updated@example.com"}
    response = await client.put(f"/users/{user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    assert data["is_active"] is True  # Default value, not updated

    # Update only the is_active status
    update_data = {"is_active": False}
    response = await client.put(f"/users/{user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"  # Email remains unchanged
    assert data["is_active"] is False
