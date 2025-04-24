from sqlmodel import SQLModel
from datetime import datetime

class ManagerRead(SQLModel):
    id: int
    firstname: str
    lastname: str
    relationship: str
    created_at: datetime
    updated_at: datetime
    #TODO pp_path: str | None = 

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
    #TODO pp_path: str
