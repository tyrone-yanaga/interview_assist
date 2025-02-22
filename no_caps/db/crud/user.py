# app/db/crud/user.py
from typing import Optional
from db.schemas import UserCreate
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from db.models.user import User
from core.security import get_password_hash


def update_user(
    db: Session,
    user_id: int,
    *,  # Force keyword arguments
    email: Optional[str] = None,
    password: Optional[str] = None,
    is_active: Optional[bool] = None
) -> User:
    """
    Update user information.

    Args:
        db: Database session
        user_id: ID of user to update
        email: New email (optional)
        password: New password (optional)
        is_active: New active status (optional)

    Returns:
        Updated user object

    Raises:
        HTTPException: If user not found or email already exists
    """
    # Get existing user
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {}

    # TODO I could probably create a loop to extract JSON and add k/v pairs
    # Update email if provided
    if email is not None and email != db_user.email:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        update_data["email"] = email

    # Update password if provided
    if password is not None:
        update_data["hashed_password"] = get_password_hash(password)

    # Update active status if provided
    if is_active is not None:
        update_data["is_active"] = is_active

    # Apply updates if there are any
    if update_data:
        try:
            for key, value in update_data.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Database error occurred while updating user",
            ) from e

    return db_user


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
