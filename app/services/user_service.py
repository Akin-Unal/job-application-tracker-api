import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, ResourceNotFoundError
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserRead, UserUpdate
from app.utils.pagination import PaginationParams, total_pages

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def list_users(self, params: PaginationParams) -> PaginatedResponse[UserRead]:
        users, total = self.users.list(offset=params.offset, limit=params.page_size)
        return PaginatedResponse[UserRead](
            items=[UserRead.model_validate(user) for user in users],
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=total_pages(total, params.page_size),
        )

    def get_user_for_actor(self, user_id: UUID, actor: User) -> User:
        if actor.role != UserRole.ADMIN and actor.id != user_id:
            raise AuthorizationError("You can only view your own account")
        user = self.users.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User was not found")
        return user

    def update_user_for_actor(self, user_id: UUID, payload: UserUpdate, actor: User) -> User:
        user = self.get_user_for_actor(user_id, actor)
        if actor.role != UserRole.ADMIN:
            if payload.role is not None or payload.is_active is not None:
                raise AuthorizationError("Only admins may change role or active status")
            if payload.full_name is not None:
                user.full_name = payload.full_name
            return self.users.commit(user)

        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.role is not None:
            user.role = payload.role
        if payload.is_active is not None:
            user.is_active = payload.is_active
        logger.info("Admin user_id=%s updated user_id=%s", actor.id, user.id)
        return self.users.commit(user)

    def deactivate_user(self, user_id: UUID, actor: User) -> User:
        user = self.users.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User was not found")
        user.is_active = False
        logger.info("Admin user_id=%s deactivated user_id=%s", actor.id, user.id)
        return self.users.commit(user)
