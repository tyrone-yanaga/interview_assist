# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.session import Base
from db.models.user import User
from main import app

# Use the database URL for the Dockerized database
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@db:5432/audio_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module")
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def cleanup_db(test_db):
    """
    Clean up the database after each test.
    """
    yield
    # Rollback any failed transaction
    test_db.rollback()

    try:
        # Delete all users (this will cascade to audio files with the updated models)
        test_db.query(User).delete()
        test_db.commit()
    except Exception as e:
        # If deletion fails, rollback and try again with a fresh transaction
        test_db.rollback()
        raise e
    finally:
        # Ensure the session is clean
        test_db.close()


@pytest.fixture
def auth_client(client):
    """Return a test client with authentication headers."""
    # Create a custom TestClient with auth headers
    client.headers.update({"Authorization": "Bearer test_token"})
    return client
