from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import DateTime, text, Interval
from pydantic import ConfigDict

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
    patient_id: Optional[int] = Field(default=None, foreign_key="patient.id", unique=True, ondelete="SET NULL")
    username: str = Field(unique=True)
    password_hash: str


class Manager(BaseTable, table=True):
    account_id: int = Field(foreign_key="account.id", ondelete="CASCADE")
    firstname: str
    lastname: str
    email: str = Field(unique=True)
    relationship: str
    pp_path: Optional[str] = Field(default=None, description="profile picture")


class Question(BaseTable, table=True):
    type: str
    category: str
    exercise: dict = Field(sa_type=JSON)
    account_id: int = Field(foreign_key="account.id", ondelete="CASCADE")
    created_by: Optional[int] = Field(foreign_key="manager.id", nullable=True, ondelete="SET NULL")
    edited_by: Optional[int] = Field(foreign_key="manager.id", nullable=True, ondelete="SET NULL")
    image_path: Optional[str] = Field(default=None, description="question image path")


class Result(BaseTable, table=True):
    data: dict = Field(sa_type=JSON)
    is_correct: bool


class Quiz(BaseTable, table=True):
    patient_id: int = Field(foreign_key="patient.id")


class QuizQuestion(SQLModel, table=True):
    question_id: int = Field(foreign_key="question.id", primary_key=True, ondelete="CASCADE")
    quiz_id: int = Field(foreign_key="quiz.id", primary_key=True, ondelete="CASCADE")
    result_id: int = Field(foreign_key="result.id", nullable=True, default=None, ondelete="SET NULL")
    box_number: Optional[int] = Field(default=None, nullable=True, foreign_key="leitnerparameters.box_number")


class DefaultQuestions(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str
    category: str
    exercise: dict = Field(sa_type=JSON)


class LeitnerParameters(SQLModel, table=True):
    box_number: int = Field(primary_key=True)
    leitner_delay: str = Field(sa_type=Interval)

    model_config = ConfigDict(arbitrary_types_allowed=True)