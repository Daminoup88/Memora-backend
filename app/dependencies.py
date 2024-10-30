from sqlmodel import Session, create_engine
from app.database import database
from typing import Generator

engine = create_engine(database.DATABASE_URL)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session