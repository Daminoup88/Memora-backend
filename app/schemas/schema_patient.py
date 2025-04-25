from sqlmodel import SQLModel
from datetime import date, datetime

class PatientCreate(SQLModel):
    firstname: str
    lastname: str
    birthday: date

class PatientRead(SQLModel):
    firstname: str
    lastname: str
    birthday: date
    created_at: datetime
    updated_at: datetime