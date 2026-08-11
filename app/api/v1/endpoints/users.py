"""User registration and identity endpoints."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.core.security import generate_api_key, hash_api_key
from app.db.models import User, UserProfile
from app.schemas.user import UserRegistrationRequest, UserRegistrationResponse, UserResponse

router = APIRouter(tags=["users"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    description=(
        "Create an account and receive an API key. The raw key is returned "
        "exactly once here and cannot be recovered afterwards - store it "
        "securely and send it as `Authorization: Bearer <api_key>` on every "
        "other request. This is the only endpoint that does not require auth."
    ),
)
def register_user(
    request: UserRegistrationRequest,
    db: Annotated[Session, Depends(get_db)],
):
    raw_key = generate_api_key()
    user = User(email=request.email, hashed_api_key=hash_api_key(raw_key))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    profile = UserProfile(user_id=user.id, full_name=request.full_name)
    db.add(profile)
    db.commit()
    db.refresh(user)

    return UserRegistrationResponse(
        id=user.id,
        email=user.email,
        api_key=raw_key,
        created_at=user.created_at,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated account",
    description="Confirms an API key is valid and returns the account it resolves to.",
)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
    )
