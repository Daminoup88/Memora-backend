from pydantic import ConfigDict
from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

class AccountBase(SQLModel):
    username: str

class AccountCreate(AccountBase):
    password: str

class AccountRead(AccountBase):
    id: int
    patient_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)