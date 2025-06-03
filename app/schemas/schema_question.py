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
    created_by: int | None = None
    edited_by: int | None = None

class QuestionUpdate(QuestionCreate):
    pass

class Clues(SQLModel):
    clues: list[str]