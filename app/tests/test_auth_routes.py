from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.dependencies import get_password_hash, create_access_token, verify_password

USER1 = {"first_name": "John", "last_name": "Doe", "email": "john.doe@gmail.com", "age": 30, "password": "password"}

# Test the token authentication route

def test_login_for_access_token(client: TestClient, session: Session):
    # Create a user
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    # Test the login route
    response = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_for_access_token_wrong_password(client: TestClient, session: Session):
    # Create a user
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    # Test the login route with wrong password
    response = client.post("/api/auth/token", data={"username": USER1["email"], "password": "wrong_password"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_wrong_email(client: TestClient, session: Session):
    # Create a user
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    # Test the login route with wrong email
    response = client.post("/api/auth/token", data={"username": "wrongemail@mail.com", "password": USER1["password"]})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_user_not_found(client: TestClient):
    # Test the login route with no user
    response = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_no_user(client: TestClient):
    # Test the login route with no user
    response = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_for_access_token_no_data(client: TestClient):
    # Test the login route with no data
    response = client.post("/api/auth/token")
    assert response.status_code == 422

def test_login_for_access_token_no_username(client: TestClient):
    # Test the login route with no username
    response = client.post("/api/auth/token", data={"password": USER1["password"]})
    assert response.status_code == 422

def test_login_for_access_token_no_password(client: TestClient):
    # Test the login route with no password
    response = client.post("/api/auth/token", data={"username": USER1["email"]})
    assert response.status_code == 422

def test_login_for_access_token_wrong_format(client: TestClient):
    # Test the login route with no username and password
    response = client.post("/api/auth/token", data={"wrong_key": "wrong_value"})
    assert response.status_code == 422