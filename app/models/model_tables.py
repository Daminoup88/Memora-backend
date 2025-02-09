from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import JSON


class Patient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    firstname: str
    lastname: str
    birthday: date


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: Optional[int] = Field(default=None, foreign_key="patient.id", unique=True)
    username: str = Field(unique=True)
    password_hash: str
    created_at: datetime


class Manager(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: Optional[int] = Field(default=None, foreign_key="account.id")
    firstname: str
    lastname: str
    email: str = Field(unique=True)
    relationship: str
    pp_path: Optional[str] = Field(default=None, description="profile picture")
    created_at: datetime
    edited_at: datetime


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str
    category: str
    exercise: dict = Field(sa_type=JSON)
    created_by: int = Field(foreign_key="manager.id")
    created_at: datetime
    edited_by: int = Field(foreign_key="manager.id")
    # on update, set to current timestamp
    edited_at: datetime


class Result(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    answered_at: datetime
    data: dict = Field(sa_type=JSON)
    is_correct: bool


class Quiz(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime
    patient_id: int = Field(foreign_key="patient.id")


class QuizQuestion(SQLModel, table=True):
    Question_id: int = Field(foreign_key="question.id", primary_key=True)
    Quiz_id: int = Field(foreign_key="quiz.id", primary_key=True)
    Result_id: int = Field(foreign_key="result.id")
    box_number: int