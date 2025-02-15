# app/api/v1/endpoints/user.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from db.session import get_db
from db.crud import user as user_crud


class UserUpdate(BaseModel):
    """Schema for user update requests"""

    email: Optional[EmailStr] = None
    password: Optional[constr(min_length=8)] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


router = APIRouter()


@router.post("/users/")
def create_user(email: str, password: str, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_email(db, email=email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_crud.create_user(db=db, email=email, password=password)


# TODO this may need to be updated for JWT tokens,
# or caller can extract email
@router.get("/get_user/")
def get_user(db: Session, id: int):
    db_user = user_crud.get_user(db, user_id=id)
    return db_user


@router.put("/users/{user_id}", response_model=UserUpdate)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: Session = Depends(get_db),
):
    """
    Update any user's information.
    This endpoint should be restricted to admin users in a real application.
    """
    # Here you might want to add admin check
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not authorized")

    updated_user = user_crud.update_user(
        db,
        user_id=user_id,
        email=update_data.email,
        password=update_data.password,
        is_active=update_data.is_active,
    )

    return UserUpdate(
        email=updated_user.email,
        is_active=updated_user.is_active)
