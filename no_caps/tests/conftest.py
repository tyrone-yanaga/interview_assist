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
TestingSessionLocal = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)

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
    # Delete all users
    test_db.query(User).delete()
    test_db.commit()
