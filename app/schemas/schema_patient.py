from sqlmodel import SQLModel
from datetime import datetime

class PatientSchema(SQLModel):
    firstname: str
    lastname: str
    birthday: datetime