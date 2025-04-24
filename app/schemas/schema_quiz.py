from sqlmodel import SQLModel
from datetime import datetime
from app.schemas.schema_question import QuestionRead

class QuizRead(SQLModel):
    id: int
    questions: list[QuestionRead]

class ResultRead(SQLModel):
    data: dict
    is_correct: bool