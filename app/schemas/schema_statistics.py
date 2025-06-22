from sqlmodel import SQLModel
from datetime import datetime
from typing import Optional, Dict, Any
from app.schemas.schema_question import QuestionRead

class QuestionSuccessRate(SQLModel):
    question: QuestionRead
    success_rate: float

class StatisticsRead(SQLModel):
    global_success_rate: float
    category_success_rate: dict[str, float]
    question_success_rate: dict[str, QuestionSuccessRate]
    leitner_box_numbers: dict[int, int]

class RegularityStats(SQLModel):
    consecutive_days: int
    quizzes_this_week: int
    average_quizzes_per_week: float
    last_quiz_date: Optional[datetime]
    total_days_active: int
    longest_streak: int
    current_streak: int
