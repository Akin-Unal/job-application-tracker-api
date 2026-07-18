from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str = Field(examples=["Operation completed successfully"])
