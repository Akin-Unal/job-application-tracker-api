from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(func.lower(User.email) == email.lower())
        return self.db.scalar(statement)

    def list(self, offset: int, limit: int) -> tuple[list[User], int]:
        total = self.db.scalar(select(func.count()).select_from(User)) or 0
        statement = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(statement)), total

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.get(user_id)
