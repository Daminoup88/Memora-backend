from sqlmodel import SQLModel
from datetime import datetime
from app.schemas.schema_question import QuestionRead

class QuizzGet(SQLModel):
    questions: list[QuestionRead]