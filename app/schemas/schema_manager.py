from sqlmodel import SQLModel
from datetime import date

class ManagerRead(SQLModel):
    firstname: str
    lastname: str
    relationship: str
    #TODO pp_path: str | None = 

class ManagerCreate(SQLModel):
    firstname: str
    lastname: str
    relationship: str
    email: str

class ManagerChange(SQLModel):
    firstname: str
    lastname: str
    relationship: str
    email: str 
    #TODO pp_path: str
