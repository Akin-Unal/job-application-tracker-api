from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_database_session
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    description="Creates a normal active user account.",
)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_database_session)],
) -> User:
    return AuthService(db).register(payload)


@router.post(
    "/login",
    response_model=Token,
    summary="Log in",
    description="Authenticates an email and password and returns a bearer access token.",
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_database_session)],
) -> Token:
    return AuthService(db).login(payload.email, payload.password)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Returns the active user associated with the bearer token.",
)
def me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user
