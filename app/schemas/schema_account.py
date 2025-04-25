from sqlmodel import SQLModel
from datetime import datetime

class AccountCreate(SQLModel):
    username: str
    password: str

class AccountRead(SQLModel):
    username: str
    created_at: datetime
    updated_at: datetime