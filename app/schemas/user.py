from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    age: int
    hashed_password: str

class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    age: int

    class Config:
        from_attributes = True