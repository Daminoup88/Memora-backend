from sqlmodel import SQLModel
from datetime import date

class PatientSchema(SQLModel):
    firstname: str
    lastname: str
    birthday: date