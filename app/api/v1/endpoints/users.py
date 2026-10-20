"""User registration and identity endpoints."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.core.security import generate_api_key, hash_api_key, make_signed_token, read_signed_token
from app.core.config import settings
from app.db.models import User, UserProfile
from app.schemas.user import ApiKeyRotationResponse, UserRegistrationRequest, UserRegistrationResponse, UserResponse

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


@router.post("/api-key/rotate", response_model=ApiKeyRotationResponse)
def rotate_api_key(current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    """Replace an API key. The new key is deliberately returned once only."""
    raw_key = generate_api_key()
    current_user.hashed_api_key = hash_api_key(raw_key)
    db.commit()
    db.refresh(current_user)
    return ApiKeyRotationResponse(api_key=raw_key, rotated_at=current_user.updated_at)


@router.post("/magic-link", status_code=status.HTTP_202_ACCEPTED)
def request_magic_link(email: str, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.email == email.lower()).first()
    if user:
        token = make_signed_token(str(user.id), "magic-link")
        logger.info("Development magic link for %s: %s/auth/verify?token=%s", email, settings.frontend_url, token)
    return {"message": "If the account exists, a sign-in link has been sent."}


@router.post("/magic-link/verify")
def verify_magic_link(token: str, response: Response, db: Annotated[Session, Depends(get_db)]):
    user_id = read_signed_token(token, "magic-link")
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active: raise HTTPException(status_code=401, detail="Invalid or expired sign-in link")
    response.set_cookie("resume_session", make_signed_token(f"{user.id}|{user.session_version}", "session", 60 * 60 * 24 * 7), httponly=True, samesite="lax", secure=False, max_age=60 * 60 * 24 * 7)
    return {"id": str(user.id), "email": user.email}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    """Remove the browser session cookie; API keys remain separately manageable."""
    current_user.session_version += 1
    db.commit()
    response.delete_cookie("resume_session", httponly=True, samesite="lax", secure=False)
