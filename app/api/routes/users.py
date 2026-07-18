from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user, require_admin
from app.api.dependencies.database import get_database_session
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService
from app.utils.pagination import PaginationParams, get_pagination_params

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    summary="List users",
    description="Lists users with pagination. Admin access is required.",
)
def list_users(
    params: Annotated[PaginationParams, Depends(get_pagination_params)],
    db: Annotated[Session, Depends(get_database_session)],
    _: Annotated[User, Depends(require_admin)],
) -> PaginatedResponse[UserRead]:
    return UserService(db).list_users(params)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user",
    description="Admins may get any user. Normal users may only get themselves.",
)
def get_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return UserService(db).get_user_for_actor(user_id, current_user)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update user",
    description="Updates a user. Admins may change roles and active status.",
)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return UserService(db).update_user_for_actor(user_id, payload, current_user)


@router.delete(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Deactivate user",
    description="Soft deletes a user by setting is_active to false. Admin access is required.",
)
def delete_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(require_admin)],
) -> User:
    return UserService(db).deactivate_user(user_id, current_user)
