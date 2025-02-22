# app/api/v1/endpoints/user.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.session import get_db
from db.crud import user as user_crud
from db.schemas import UserCreate, UserResponse, UserUpdate, UserList
from db.models.user import User  # Import SQLAlchemy model instead of Pydantic model

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_crud.create_user(db=db, user=user)


@router.get("/", response_model=UserList)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    users = db.query(User).offset(skip).limit(limit).all()  # Use SQLAlchemy User model
    total = db.query(User).count()
    return {"items": users, "total": total}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
):
    """Update user information."""
    return user_crud.update_user(
        db,
        user_id=user_id,
        email=update_data.email,
        password=update_data.password,
        is_active=update_data.is_active,
    )
