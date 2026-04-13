"""Common shared schemas used across the API."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response envelope.

    Attributes:
        items: List of result items.
        total: Total matching count.
        page: Current page number.
        per_page: Items per page.
        pages: Total number of pages.
    """

    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class ErrorResponse(BaseModel):
    """Standardized error response body.

    Attributes:
        detail: Human-readable error message.
        code: Machine-readable error code.
    """

    detail: str
    code: str
