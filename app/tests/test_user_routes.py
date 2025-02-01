from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.model_user import User
from app.schemas.schema_user import UserCreate, UserRead
from app.dependencies import get_password_hash, create_access_token, verify_password

USER1 = {"first_name": "John", "last_name": "Doe", "email": "john.doe@gmail.com", "age": 30, "password": "password"}
USER2 = {"first_name": "Jane", "last_name": "Doe", "email": "jane.doe@gmail.com", "age": 25, "password": "password"}

def test_create_user(client: TestClient, session: Session):
    # create user
    response = client.post("/api/users/", json=USER1)
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == USER1["first_name"]
    assert data["last_name"] == USER1["last_name"]
    assert data["email"] == USER1["email"]
    assert data["age"] == USER1["age"]
    assert UserRead(**data)
    assert "hashed_password" not in data
    # query database
    user = session.exec(select(User).where(User.email == USER1["email"])).first()
    # check database
    assert user is not None
    assert user.first_name == USER1["first_name"]
    assert user.last_name == USER1["last_name"]
    assert user.email == USER1["email"]
    assert user.age == USER1["age"]
    assert user.hashed_password != USER1["password"]
    assert verify_password(USER1["password"], user.hashed_password)

def test_create_user_invalid_email_no_at(client: TestClient, session: Session):
    # create user with invalid email (no @)
    user_no_at_email = USER1.copy()
    user_no_at_email["email"] = "invalid_email"
    response = client.post("/api/users/", json=user_no_at_email)
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("value is not a valid email address")
    # check database (no user created)
    assert session.exec(select(User).where(User.email == user_no_at_email["email"])).first() is None

def test_create_user_invalid_email_double_at(client: TestClient, session: Session):
    # create user with invalid email (double @)
    user_double_at_email = USER1.copy()
    user_double_at_email["email"] = "invalid@@_email"
    response = client.post("/api/users/", json=user_double_at_email)
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("value is not a valid email address")
    # database check (no user created)
    assert session.exec(select(User).where(User.email == user_double_at_email["email"])).first() is None

def test_create_user_double_email(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    # create user with same email via API
    response = client.post("/api/users/", json=USER1)
    # check response
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered"
    # check database (only one user created)
    users = session.exec(select(User).where(User.email == USER1["email"])).all()
    assert len(users) == 1

def test_create_user_invalid_body(client: TestClient, session: Session):
    # create user with invalid body (missing fields)
    response = client.post("/api/users/", json={})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert len(data["detail"]) == 5
    assert data["detail"][0]["loc"] == ["body", "first_name"] and data["detail"][0]["msg"] == "Field required"
    assert data["detail"][1]["loc"] == ["body", "last_name"] and data["detail"][1]["msg"] == "Field required"
    assert data["detail"][2]["loc"] == ["body", "email"] and data["detail"][2]["msg"] == "Field required"
    assert data["detail"][3]["loc"] == ["body", "age"] and data["detail"][3]["msg"] == "Field required"
    assert data["detail"][4]["loc"] == ["body", "password"] and data["detail"][4]["msg"] == "Field required"
    # check database (no user created)
    assert session.exec(select(User)).all() == []

# def test_create_user_already_logged_in(client: TestClient, session: Session):
#     # create user in database
#     USER1_hashed = USER1.copy()
#     USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
#     session.add(User(**USER1_hashed))
#     session.commit()
#     # create user while logged in
#     token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
#     response = client.post("/api/users/", json=USER2, headers={"Authorization": f"Bearer {token}"})
#     # check response
#     assert response.status_code == 403
#     data = response.json()
#     assert data["detail"] == "User already authenticated"
#     # check database (only one user created)
#     users = session.exec(select(User)).all()
#     assert len(users) == 1
#     assert users[0].first_name == USER1["first_name"]
#     assert users[0].last_name == USER1["last_name"]
#     assert users[0].email == USER1["email"]
#     assert verify_password(USER1["password"], users[0].hashed_password)

def test_read_user(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    # read user via API
    token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
    response = client.get("/api/users/", headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == USER1_hashed["first_name"]
    assert data["last_name"] == USER1_hashed["last_name"]
    assert data["email"] == USER1_hashed["email"]
    assert data["age"] == USER1_hashed["age"]
    assert UserRead(**data)
    assert "hashed_password" not in data

def test_read_user_not_found(client: TestClient):
    # create fake access token
    fake_access_token = create_access_token(data={"sub": 1})
    # read user not in database
    response = client.get("/api/users/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_read_user_invalid_id(client: TestClient):
    # read user with invalid id
    fake_access_token = create_access_token(data={"sub": "invalid_id"})
    # read user not in database
    response = client.get("/api/users/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"
    
def test_read_user_invalid_token(client: TestClient):
    # read user with invalid token
    response = client.get("/api/users/", headers={"Authorization": "Bearer invalid_token"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_read_user_not_logged_in(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    # read user without logging in
    response = client.get("/api/users/")
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

def test_update_user(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    user_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    # update user via API
    updated_user = USER1.copy()
    updated_user["first_name"] = "Jane"
    updated_user["last_name"] = "Smith"
    updated_user["password"] = "new_password"
    token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
    response = client.put("/api/users/", json=updated_user, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == updated_user["first_name"]
    assert data["last_name"] == updated_user["last_name"]
    assert data["email"] == updated_user["email"]
    assert data["age"] == updated_user["age"]
    assert "hashed_password" not in data
    # check database
    user = session.get(User, user_id)
    assert user.id == data["id"]
    assert user.first_name == updated_user["first_name"]
    assert user.last_name == updated_user["last_name"]
    assert user.email == updated_user["email"]
    assert user.age == updated_user["age"]
    assert user.hashed_password != updated_user["password"]
    assert UserRead(**data)
    assert verify_password(updated_user["password"], user.hashed_password)

def test_update_user_not_found(client: TestClient):
    # create fake access token
    fake_access_token = create_access_token(data={"sub": 1})
    # update user not in database
    response = client.put("/api/users/", json=USER1, headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_update_user_invalid_id(client: TestClient):
    # update user with invalid id
    fake_access_token = create_access_token(data={"sub": "invalid_id"})
    response = client.put("/api/users/", json=USER1, headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_update_user_invalid_token(client: TestClient):
    # update user with invalid token
    response = client.put("/api/users/", json=USER1, headers={"Authorization": "Bearer invalid_token"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_update_user_invalid_body(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    user_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    # update user with invalid body (missing fields)
    token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
    response = client.put("/api/users/", json={}, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert len(data["detail"]) == 5
    assert data["detail"][0]["loc"] == ["body", "first_name"] and data["detail"][0]["msg"] == "Field required"
    assert data["detail"][1]["loc"] == ["body", "last_name"] and data["detail"][1]["msg"] == "Field required"
    assert data["detail"][2]["loc"] == ["body", "email"] and data["detail"][2]["msg"] == "Field required"
    assert data["detail"][3]["loc"] == ["body", "age"] and data["detail"][3]["msg"] == "Field required"
    assert data["detail"][4]["loc"] == ["body", "password"] and data["detail"][4]["msg"] == "Field required"
    # check database
    user = session.get(User, user_id)
    assert user.first_name == USER1_hashed["first_name"]
    assert user.last_name == USER1_hashed["last_name"]
    assert user.email == USER1_hashed["email"]
    assert user.age == USER1_hashed["age"]
    assert user.hashed_password == USER1_hashed["hashed_password"]

def test_update_user_double_email(client: TestClient, session: Session):
    # create two users in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    USER2_hashed = USER2.copy()
    USER2_hashed["hashed_password"] = get_password_hash(USER2_hashed.pop("password"))
    session.add(User(**USER2_hashed))
    session.commit()
    user1_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    user2_id = session.exec(select(User).where(User.email == USER2["email"])).first().id
    # update user1 with email from user2
    updated_user = USER1.copy()
    updated_user["email"] = USER2["email"]
    updated_user["password"] = "new_password"
    token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
    response = client.put(f"/api/users/", json=updated_user, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered"
    # check database
    user1 = session.get(User, user1_id)
    user2 = session.get(User, user2_id)
    assert user1.email == USER1["email"]
    assert user2.email == USER2["email"]
    assert verify_password(USER1["password"], user1.hashed_password)

def test_update_user_invalid_email_no_at(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    user_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    # update user with invalid email (no @)
    updated_user = USER1.copy()
    updated_user["email"] = "invalid_email"
    updated_user["password"] = "new_password"
    token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
    response = client.put(f"/api/users/", json=updated_user, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("value is not a valid email address")
    # check database
    user = session.get(User, user_id)
    assert user.email == USER1["email"]
    assert verify_password(USER1["password"], user.hashed_password)

def test_update_user_invalid_email_double_at(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    user_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    # update user with invalid email (double @)
    updated_user = USER1.copy()
    updated_user["email"] = "invalid@@email"
    updated_user["password"] = "new_password"
    token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
    response = client.put(f"/api/users/", json=updated_user, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("value is not a valid email address")
    # check database
    user = session.get(User, user_id)
    assert user.email == USER1["email"]
    assert verify_password(USER1["password"], user.hashed_password)

def test_update_user_not_logged_in(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    user_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    # update user without logging in
    updated_user = USER1.copy()
    updated_user["password"] = "new_password"
    response = client.put("/api/users/", json=updated_user)
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"
    # check database
    user = session.get(User, user_id)
    assert user.email == USER1["email"]
    assert verify_password(USER1["password"], user.hashed_password)

def test_delete_user(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    user_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    # delete user via API
    token = client.post("/api/auth/token", data={"username": USER1["email"], "password": USER1["password"]}).json()["access_token"]
    response = client.delete("/api/users/", headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data == {"detail": "User deleted successfully"}
    # check database
    user = session.get(User, user_id)
    assert user is None
    
def test_delete_user_not_found(client: TestClient):
    # create fake access token
    fake_access_token = create_access_token(data={"sub": 1})
    # delete user not in database
    response = client.delete("/api/users/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_delete_user_invalid_id(client: TestClient):
    # delete user with invalid id
    fake_access_token = create_access_token(data={"sub": "invalid_id"})
    response = client.delete("/api/users/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_delete_user_invalid_token(client: TestClient):
    # delete user with invalid token
    response = client.delete("/api/users/", headers={"Authorization": "Bearer invalid_token"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_delete_user_not_logged_in(client: TestClient, session: Session):
    # create user in database
    USER1_hashed = USER1.copy()
    USER1_hashed["hashed_password"] = get_password_hash(USER1_hashed.pop("password"))
    session.add(User(**USER1_hashed))
    session.commit()
    user_id = session.exec(select(User).where(User.email == USER1["email"])).first().id
    # delete user without logging in
    response = client.delete("/api/users/")
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"
    # check database
    user = session.get(User, user_id)
    assert user is not None
    assert verify_password(USER1["password"], user.hashed_password)
    assert user.first_name == USER1["first_name"]
    assert user.last_name == USER1["last_name"]
    assert user.email == USER1["email"]
    assert user.age == USER1["age"]