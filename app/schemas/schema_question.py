from sqlmodel import SQLModel
from datetime import datetime

class QuestionCreate(SQLModel):
    type: str
    category: str
    exercise: dict

class QuestionRead(SQLModel):
    id: int
    type: str
    category: str
    exercise: dict
    created_at: datetime
    updated_at: datetime

class QuestionUpdate(SQLModel):
    pass