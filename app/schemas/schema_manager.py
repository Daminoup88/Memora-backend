from sqlmodel import SQLModel
from datetime import datetime
from app.schemas.schema_pagination import PaginatedResponse

class ManagerRead(SQLModel):
    id: int
    firstname: str
    lastname: str
    relationship: str
    created_at: datetime
    updated_at: datetime
    pp_path: str | None = None

class ManagerCreate(SQLModel):
    firstname: str
    lastname: str
    relationship: str
    email: str

class ManagerUpdate(SQLModel):
    firstname: str
    lastname: str
    relationship: str
    email: str

# Alias pour la réponse paginée de managers
PaginatedManagersResponse = PaginatedResponse[ManagerRead]
