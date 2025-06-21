from sqlmodel import SQLModel
from typing import Generic, TypeVar

T = TypeVar('T')

class PaginationMeta(SQLModel):
    """Métadonnées de pagination"""
    page: int
    size: int
    total: int
    pages: int

class PaginatedResponse(SQLModel, Generic[T]):
    """Réponse paginée générique"""
    items: list[T]
    meta: PaginationMeta
