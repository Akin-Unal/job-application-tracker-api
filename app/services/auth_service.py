import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ResourceAlreadyExistsError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, Token

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> User:
        if self.users.get_by_email(payload.email):
            raise ResourceAlreadyExistsError("A user with this email already exists")
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=UserRole.USER,
        )
        return self.users.add(user)

    def login(self, email: str, password: str) -> Token:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password) or not user.is_active:
            logger.info("Authentication failure for email=%s", email)
            raise AuthenticationError("Invalid email or password")
        return Token(access_token=create_access_token(str(user.id)))
