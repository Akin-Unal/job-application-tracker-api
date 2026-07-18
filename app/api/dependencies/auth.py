from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_database_session
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_database_session)],
) -> User:
    if credentials is None:
        raise AuthenticationError()
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthenticationError() from exc
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise AuthenticationError()
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise AuthenticationError("Inactive user")
    return current_user


def require_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin privileges are required")
    return current_user
