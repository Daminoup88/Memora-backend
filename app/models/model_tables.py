from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import DateTime, text

class BaseTable(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("TIMEZONE('Europe/Paris', NOW())")},
        nullable=False,
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": text("TIMEZONE('Europe/Paris', NOW())"),
            "onupdate": text("TIMEZONE('Europe/Paris', NOW())"),
        },
    )


class Patient(BaseTable, table=True):
    firstname: str
    lastname: str
    birthday: date


class Account(BaseTable, table=True):
    patient_id: Optional[int] = Field(default=None, foreign_key="patient.id", unique=True)
    username: str = Field(unique=True)
    password_hash: str


class Manager(BaseTable, table=True):
    account_id: Optional[int] = Field(default=None, foreign_key="account.id")
    firstname: str
    lastname: str
    email: str = Field(unique=True)
    relationship: str
    pp_path: Optional[str] = Field(default=None, description="profile picture")


class Question(BaseTable, table=True):
    type: str
    category: str
    exercise: dict = Field(sa_type=JSON)
    created_by: int = Field(foreign_key="manager.id")
    edited_by: int = Field(foreign_key="manager.id")


class Result(BaseTable, table=True):
    data: dict = Field(sa_type=JSON)
    is_correct: bool


class Quiz(BaseTable, table=True):
    patient_id: int = Field(foreign_key="patient.id")


class QuizQuestion(SQLModel, table=True):
    question_id: int = Field(foreign_key="question.id", primary_key=True)
    quiz_id: int = Field(foreign_key="quiz.id", primary_key=True)
    result_id: int = Field(foreign_key="result.id")
    box_number: int