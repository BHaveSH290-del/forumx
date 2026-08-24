from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.models import User
from app.schemas.user import UserCreate, UserRead


router = APIRouter(prefix="/users", tags=["users"])
password_hash = PasswordHash.recommended()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db_session),
) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=password_hash.hash(user_in.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        constraint_name = getattr(exc.orig, "diag", None)
        constraint_name = getattr(constraint_name, "constraint_name", "")

        if constraint_name == "uq_users_username":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists.",
            ) from exc

        if constraint_name == "uq_users_email":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user.",
        ) from exc

    db.refresh(user)
    return user
