from sqlmodel import SQLModel

class StatisticsRead(SQLModel):
    global_success_rate: float
    category_success_rate: dict[str, float]
    question_success_rate: dict[int, float]
    leitner_box_numbers: dict[int, int]
