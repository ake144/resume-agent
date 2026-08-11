"""Authentication dependency: resolves the caller's API key to a User."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_api_key
from app.db.models import User

# auto_error=False so both "missing header" and "invalid key" can be raised
# uniformly as 401 below - HTTPBearer's own auto_error path returns 403 for
# a missing header, which is inconsistent with the invalid-key case.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the Authorization: Bearer <api_key> header to an active User.

    Deliberately a plain `def`, not `async def`: this does a blocking sync
    Session query. As a sync function FastAPI runs it in its threadpool
    automatically, so the event loop is never blocked on it.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or not credentials.credentials:
        raise unauthorized

    hashed = hash_api_key(credentials.credentials)
    user = db.query(User).filter(User.hashed_api_key == hashed).first()

    if user is None or not user.is_active:
        raise unauthorized

    return user
