# app/db/crud/user.py
from typing import Optional
from db.schemas import UserCreate
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from db.models.user import User
from core.security import get_password_hash, verify_password
from passlib.context import CryptContext


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User's email
        password: User's password

    Returns:
        User: The user object if authentication successful, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# Modify your existing create_user function to hash passwords:


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user with hashed password.

    Args:
        db: Database session
        user: User creation data with plain text password

    Returns:
        User: The created user
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# If you have an update_user function, modify it to handle password changes:


def update_user(
    db: Session,
    user_id: int,
    email: Optional[str] = None,
    password: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[User]:
    """
    Update user information.

    Args:
        db: Database session
        user_id: ID of the user to update
        email: New email (optional)
        password: New password (optional)
        is_active: New active status (optional)

    Returns:
        Optional[User]: The updated user, or raises an HTTPException 
        if update fails.
    """
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if email is not None and email != db_user.email:
            existing_user = get_user_by_email(db, email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            db_user.email = email

        if password is not None:
            db_user.hashed_password = get_password_hash(password)

        if is_active is not None:
            db_user.is_active = is_active

        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Error updating user"
        ) from e
