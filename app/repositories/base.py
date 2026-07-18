from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.database.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, item_id: UUID) -> ModelT | None:
        return self.db.get(self.model, item_id)

    def add(self, item: ModelT) -> ModelT:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def commit(self, item: ModelT) -> ModelT:
        self.db.commit()
        self.db.refresh(item)
        return item
