from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.user import User

USER1 = {"first_name": "John", "last_name": "Doe", "email": "john.doe@gmail.com", "age": 30, "hashed_password": "hashed_password"}
USER2 = {"first_name": "Jane", "last_name": "Doe", "email": "jane.doe@gmail.com", "age": 25, "hashed_password": "hashed_password"}

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
    assert "id" in data and isinstance(data["id"], int)
    assert "hashed_password" not in data
    # query database
    user = session.exec(select(User).where(User.email == USER1["email"])).first()
    # check database
    assert user is not None
    assert user.first_name == USER1["first_name"]
    assert user.last_name == USER1["last_name"]
    assert user.email == USER1["email"]
    assert user.age == USER1["age"]
    assert user.hashed_password == USER1["hashed_password"]

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
    session.add(User(**USER1))
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
    assert data["detail"][4]["loc"] == ["body", "hashed_password"] and data["detail"][4]["msg"] == "Field required"
    # check database (no user created)
    assert session.exec(select(User)).all() == []

def test_read_user(client: TestClient, session: Session):
    # create user in database
    user = User(**USER1)
    session.add(user)
    session.commit()
    # read user via API
    response = client.get(f"/api/users/{user.id}")
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == user.first_name
    assert data["last_name"] == user.last_name
    assert data["email"] == user.email
    assert data["age"] == user.age
    assert data["id"] == user.id
    assert "hashed_password" not in data

def test_read_user_not_found(client: TestClient, session: Session):
    # read user not in database
    response = client.get("/api/users/1")
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_read_user_invalid_id(client: TestClient, session: Session):
    # read user with invalid id
    response = client.get("/api/users/invalid_id")
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("Input should be a valid integer")

def test_update_user(client: TestClient, session: Session):
    # create user in database
    user = User(**USER1)
    session.add(user)
    session.commit()
    # update user via API
    updated_user = USER1.copy()
    updated_user["first_name"] = "Jane"
    response = client.put(f"/api/users/{user.id}", json=updated_user)
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == updated_user["first_name"]
    assert data["last_name"] == user.last_name
    assert data["email"] == user.email
    assert data["age"] == user.age
    assert data["id"] == user.id
    assert "hashed_password" not in data
    # check database
    user = session.get(User, user.id)
    assert user.first_name == updated_user["first_name"]
    assert user.last_name == USER1["last_name"]
    assert user.email == USER1["email"]
    assert user.age == USER1["age"]
    assert user.hashed_password == USER1["hashed_password"]

def test_update_user_not_found(client: TestClient, session: Session):
    # update user not in database
    response = client.put("/api/users/1", json=USER1)
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_update_user_invalid_id(client: TestClient, session: Session):
    # update user with invalid id
    response = client.put("/api/users/invalid_id", json=USER1)
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("Input should be a valid integer")

def test_update_user_invalid_body(client: TestClient, session: Session):
    # create user in database
    user = User(**USER1)
    session.add(user)
    session.commit()
    # update user with invalid body (missing fields)
    response = client.put(f"/api/users/{user.id}", json={})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert len(data["detail"]) == 5
    assert data["detail"][0]["loc"] == ["body", "first_name"] and data["detail"][0]["msg"] == "Field required"
    assert data["detail"][1]["loc"] == ["body", "last_name"] and data["detail"][1]["msg"] == "Field required"
    assert data["detail"][2]["loc"] == ["body", "email"] and data["detail"][2]["msg"] == "Field required"
    assert data["detail"][3]["loc"] == ["body", "age"] and data["detail"][3]["msg"] == "Field required"
    assert data["detail"][4]["loc"] == ["body", "hashed_password"] and data["detail"][4]["msg"] == "Field required"
    # check database
    user = session.get(User, user.id)
    assert user.first_name == USER1["first_name"]
    assert user.last_name == USER1["last_name"]
    assert user.email == USER1["email"]
    assert user.age == USER1["age"]
    assert user.hashed_password == USER1["hashed_password"]

def test_update_user_double_email(client: TestClient, session: Session):
    # create two users in database
    user1 = User(**USER1)
    user2 = User(**USER2)
    session.add(user1)
    session.add(user2)
    session.commit()
    session.refresh(user1)
    session.refresh(user2)
    # update user1 with email from user2
    updated_user = USER1.copy()
    updated_user["email"] = USER2["email"]
    response = client.put(f"/api/users/{user1.id}", json=updated_user)
    # check response
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered"
    # check database
    user1 = session.get(User, user1.id)
    user2 = session.get(User, user2.id)
    assert user1.email == USER1["email"]
    assert user2.email == USER2["email"]

def test_update_user_invalid_email_no_at(client: TestClient, session: Session):
    # create user in database
    user = User(**USER1)
    session.add(user)
    session.commit()
    # update user with invalid email (no @)
    updated_user = USER1.copy()
    updated_user["email"] = "invalid_email"
    response = client.put(f"/api/users/{user.id}", json=updated_user)
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("value is not a valid email address")
    # check database
    user = session.get(User, user.id)
    assert user.email == USER1["email"]

def test_update_user_invalid_email_double_at(client: TestClient, session: Session):
    # create user in database
    user = User(**USER1)
    session.add(user)
    session.commit()
    # update user with invalid email (double @)
    updated_user = USER1.copy()
    updated_user["email"] = "invalid@@_email"
    response = client.put(f"/api/users/{user.id}", json=updated_user)
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("value is not a valid email address")
    # check database
    user = session.get(User, user.id)
    assert user.email == USER1["email"]

def test_delete_user(client: TestClient, session: Session):
    # create user in database
    user = User(**USER1)
    session.add(user)
    session.commit()
    # delete user via API
    response = client.delete(f"/api/users/{user.id}")
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "User deleted successfully"}
    # check database
    assert session.get(User, user.id) is None

def test_delete_user_not_found(client: TestClient, session: Session):
    # delete user not in database
    response = client.delete("/api/users/1")
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"

def test_delete_user_invalid_id(client: TestClient, session: Session):
    # delete user with invalid id
    response = client.delete("/api/users/invalid_id")
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("Input should be a valid integer")