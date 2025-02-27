from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.model_tables import Account
from app.schemas.schema_account import AccountCreate, AccountRead
from app.dependencies import get_password_hash, create_access_token, verify_password

ACCOUNT1 = {"username": "John", "password": "pwd123"}

# Test the token authentication route

def test_login_for_access_token(client: TestClient, session: Session):
    # Create an account
    ACCOUNT1_hashed = ACCOUNT1.copy()
    ACCOUNT1_hashed["password_hash"] = get_password_hash(ACCOUNT1_hashed.pop("password"))
    session.add(Account(**ACCOUNT1_hashed))
    session.commit()
    # Test the login route
    response = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_for_access_token_wrong_password(client: TestClient, session: Session):
    # Create an account
    ACCOUNT1_hashed = ACCOUNT1.copy()
    ACCOUNT1_hashed["password_hash"] = get_password_hash(ACCOUNT1_hashed.pop("password"))
    session.add(Account(**ACCOUNT1_hashed))
    session.commit()
    # Test the login route with wrong password
    response = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": "wrong_password"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_wrong_username(client: TestClient, session: Session):
    # Create an account
    ACCOUNT1_hashed = ACCOUNT1.copy()
    ACCOUNT1_hashed["password_hash"] = get_password_hash(ACCOUNT1_hashed.pop("password"))
    session.add(Account(**ACCOUNT1_hashed))
    session.commit()
    # Test the login route with wrong username
    response = client.post("/api/auth/token", data={"username": "wrongusername", "password": ACCOUNT1["password"]})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_account_not_found(client: TestClient):
    # Test the login route with no account
    response = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_no_data(client: TestClient):
    # Test the login route with no data
    response = client.post("/api/auth/token")
    assert response.status_code == 422

def test_login_for_access_token_no_username(client: TestClient):
    # Test the login route with no username
    response = client.post("/api/auth/token", data={"password": ACCOUNT1["password"]})
    assert response.status_code == 422

def test_login_for_access_token_no_password(client: TestClient):
    # Test the login route with no password
    response = client.post("/api/auth/token", data={"username": ACCOUNT1["username"]})
    assert response.status_code == 422

def test_login_for_access_token_wrong_format(client: TestClient):
    # Test the login route with wrong data format
    response = client.post("/api/auth/token", data={"wrong_key": "wrong_value"})
    assert response.status_code == 422
