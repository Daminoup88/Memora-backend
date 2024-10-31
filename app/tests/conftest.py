import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app
from app.dependencies import get_session
from app.database import Database

# Import the models to test to create the tables from metadata
from app.models.user import User

@pytest.fixture(name="session")
def session_fixture():
    test_database = Database(database_name="test_database")
    engine = create_engine(test_database.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()