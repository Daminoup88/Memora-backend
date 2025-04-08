import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app
from app.dependencies import get_session, get_password_hash, create_access_token
from app.database import Database

# Import the models to test to create the tables from metadata
from app.models.model_tables import Account, Manager, Patient, Question, Result, Quiz, QuizQuestion

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

@pytest.fixture
def manager1():
    return {
        "firstname": "John",
        "lastname": "Doe",
        "relationship": "Brother",
        "email": "john@example.com"
    }

@pytest.fixture
def manager2():
    return {
        "firstname": "Jane",
        "lastname": "Smith",
        "relationship": "Sister",
        "email": "jane@example.com"
    }

@pytest.fixture
def account1():
    return {"username": "managerowner", "password": "pwd123"}

@pytest.fixture
def account2():
    return {"username": "patientowner", "password": "testpwd"}

@pytest.fixture
def token(client: TestClient, session: Session, account1):
    # Create account directly in DB
    account_hashed = account1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    db_account = Account(**account_hashed)
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    # Retrieve token via API
    response = client.post("/api/auth/token", data={"username": account1["username"], "password": "pwd123"})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to retrieve token: {response.status_code} - {response.text}")