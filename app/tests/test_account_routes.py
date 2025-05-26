from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.model_tables import Account, Patient
from app.schemas.schema_account import AccountCreate, AccountRead
from app.dependencies import get_password_hash, create_access_token, verify_password

ACCOUNT1 = {"username": "John", "password": "pwd123"}
ACCOUNT2 = {"username": "Jane", "password": "password"}
# Add patient test data for combined endpoint
PATIENT1 = {"firstname": "Alice", "lastname": "Smith", "birthday": "1990-05-15"}

def test_create_account(client: TestClient, session: Session):
    # create account
    response = client.post("/api/accounts/", json=ACCOUNT1)
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == ACCOUNT1["username"]
    assert AccountRead(**data)
    assert "password" not in data
    assert "id" not in data  # Ensure 'id' is not in the response
    # query database
    account = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first()
    # check database
    assert account.username == ACCOUNT1["username"]
    assert verify_password(ACCOUNT1["password"], account.password_hash)

def test_create_account_duplicate_username(client: TestClient, session: Session):
    # create account
    response = client.post("/api/accounts/", json=ACCOUNT1)
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == ACCOUNT1["username"]
    assert AccountRead(**data)
    assert "password" not in data
    assert "id" not in data  # Ensure 'id' is not in the response
    # create account with same username
    response = client.post("/api/accounts/", json=ACCOUNT1)
    # check response
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Username already registered"
    # check database
    accounts = session.exec(select(Account)).all()
    assert len(accounts) == 1
    assert accounts[0].username == ACCOUNT1["username"]
    assert verify_password(ACCOUNT1["password"], accounts[0].password_hash)

def test_create_account_invalid_body(client: TestClient, session: Session):
    # create account with invalid body (missing fields)
    response = client.post("/api/accounts/", json={})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert len(data["detail"]) == 2
    assert data["detail"][0]["loc"] == ["body", "username"] and data["detail"][0]["msg"] == "Field required"
    assert data["detail"][1]["loc"] == ["body", "password"] and data["detail"][1]["msg"] == "Field required"
    # check database (no account created)
    assert session.exec(select(Account)).all() == []

def test_create_account_empty_username(client: TestClient, session: Session):
    return
    # create account with invalid username
    response = client.post("/api/accounts/", json={"username": "", "password": "pwd123"})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("String should have at least 1 character")
        # check database (no account created)
    assert session.exec(select(Account)).all() == []

def test_create_account_empty_password(client: TestClient, session: Session):
    return
    # create account with invalid password
    response = client.post("/api/accounts/", json={"username": "John", "password": ""})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("String should have at least 1 character")
        # check database (no account created)
    assert session.exec(select(Account)).all() == []

def test_read_account(client: TestClient, session: Session):
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    # read account via API
    token = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]}).json()["access_token"]
    response = client.get("/api/accounts/", headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == account_hashed["username"]
    assert AccountRead(**data)
    assert "password_hash" not in data
    assert "id" not in data  # Ensure 'id' is not in the response

def test_read_account_not_found(client: TestClient):
    # create fake access token
    fake_access_token = create_access_token(data={"sub": 1})
    # read account not in database
    response = client.get("/api/accounts/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Account not found"

def test_read_account_invalid_id(client: TestClient):
    # read account with invalid id
    fake_access_token = create_access_token(data={"sub": "invalid_id"})
    # read account not in database
    response = client.get("/api/accounts/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"
    
def test_read_account_invalid_token(client: TestClient):
    # read account with invalid token
    response = client.get("/api/accounts/", headers={"Authorization": "Bearer invalid_token"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_read_account_not_logged_in(client: TestClient, session: Session):
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    # read account without logging in
    response = client.get("/api/accounts/")
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"

def test_update_account(client: TestClient, session: Session):
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    account_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    # update account via API
    updated_account = ACCOUNT1.copy()
    updated_account["username"] = "Jane"
    updated_account["password"] = "new_password"
    token = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]}).json()["access_token"]
    response = client.put("/api/accounts/", json=updated_account, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == updated_account["username"]
    assert "password_hash" not in data
    assert "id" not in data  # Ensure 'id' is not in the response
    # check database
    account = session.get(Account, account_id)
    assert account.username == updated_account["username"]
    assert account.password_hash != updated_account["password"]
    assert AccountRead(**data)
    assert verify_password(updated_account["password"], account.password_hash)

def test_update_account_not_found(client: TestClient):
    # create fake access token
    fake_access_token = create_access_token(data={"sub": 1})
    # update account not in database
    response = client.put("/api/accounts/", json=ACCOUNT1, headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Account not found"

def test_update_account_invalid_id(client: TestClient):
    # update account with invalid id
    fake_access_token = create_access_token(data={"sub": "invalid_id"})
    response = client.put("/api/accounts/", json=ACCOUNT1, headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_update_account_invalid_token(client: TestClient):
    # update account with invalid token
    response = client.put("/api/accounts/", json=ACCOUNT1, headers={"Authorization": "Bearer invalid_token"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_update_account_invalid_body(client: TestClient, session: Session):
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    account_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    # update account with invalid body (missing fields)
    token = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]}).json()["access_token"]
    response = client.put("/api/accounts/", json={}, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert len(data["detail"]) == 2
    assert data["detail"][0]["loc"] == ["body", "username"] and data["detail"][0]["msg"] == "Field required"
    assert data["detail"][1]["loc"] == ["body", "password"] and data["detail"][1]["msg"] == "Field required"
        # check database
    account = session.get(Account, account_id)
    assert account.username == account_hashed["username"]
    assert account.password_hash == account_hashed["password_hash"]

def test_update_account_duplicate_username(client: TestClient, session: Session):
    # create two accounts in database
    account1_hashed = ACCOUNT1.copy()
    account1_hashed["password_hash"] = get_password_hash(account1_hashed.pop("password"))
    session.add(Account(**account1_hashed))
    account2_hashed = ACCOUNT2.copy()
    account2_hashed["password_hash"] = get_password_hash(account2_hashed.pop("password"))
    session.add(Account(**account2_hashed))
    session.commit()
    account1_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    account2_id = session.exec(select(Account).where(Account.username == ACCOUNT2["username"])).first().id
    # update account1 with username from account2
    updated_account = ACCOUNT1.copy()
    updated_account["username"] = ACCOUNT2["username"]
    updated_account["password"] = "new_password"
    token = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]}).json()["access_token"]
    response = client.put("/api/accounts/", json=updated_account, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Username already registered"
        # check database
    account1 = session.get(Account, account1_id)
    account2 = session.get(Account, account2_id)
    assert account1.username == ACCOUNT1["username"]
    assert account2.username == ACCOUNT2["username"]
    assert verify_password(ACCOUNT1["password"], account1.password_hash)

def test_update_account_not_logged_in(client: TestClient, session: Session):
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    account_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    # update account without logging in
    updated_account = ACCOUNT1.copy() 
    updated_account["password"] = "new_password"
    response = client.put("/api/accounts/", json=updated_account)
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"
        # check database
    account = session.get(Account, account_id)
    assert account.username == ACCOUNT1["username"]
    assert verify_password(ACCOUNT1["password"], account.password_hash)

def test_update_account_empty_username(client: TestClient, session: Session):
    return
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    account_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    # update account with invalid username
    updated_account = ACCOUNT1.copy()
    updated_account["username"] = ""  # Invalid empty username
    updated_account["password"] = "new_password"
    token = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]}).json()["access_token"]
    response = client.put("/api/accounts/", json=updated_account, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("String should have at least 1 character")
        # check database
    account = session.get(Account, account_id)
    assert account.username == ACCOUNT1["username"]
    assert verify_password(ACCOUNT1["password"], account.password_hash)

def test_update_account_empty_password(client: TestClient, session: Session):
    return
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    account_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    # update account with invalid password
    updated_account = ACCOUNT1.copy()
    updated_account["username"] = "newname"
    updated_account["password"] = ""  # Invalid empty password
    token = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]}).json()["access_token"]
    response = client.put("/api/accounts/", json=updated_account, headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["msg"].startswith("String should have at least 1 character")
        # check database
    account = session.get(Account, account_id)
    assert account.username == ACCOUNT1["username"]
    assert verify_password(ACCOUNT1["password"], account.password_hash)

def test_delete_account(client: TestClient, session: Session):
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    account_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    # delete account via API
    token = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]}).json()["access_token"]
    response = client.delete("/api/accounts/", headers={"Authorization": f"Bearer {token}"})
    # check response
    assert response.status_code == 200
    data = response.json()
    assert data == {"detail": "Account deleted successfully"}
        # check database
    account = session.get(Account, account_id)
    assert account is None
    
def test_delete_account_not_found(client: TestClient):
    # create fake access token
    fake_access_token = create_access_token(data={"sub": 1})
    # delete account not in database
    response = client.delete("/api/accounts/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Account not found"

def test_delete_account_invalid_id(client: TestClient):
    # delete account with invalid id
    fake_access_token = create_access_token(data={"sub": "invalid_id"})
    response = client.delete("/api/accounts/", headers={"Authorization": f"Bearer {fake_access_token}"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_delete_account_invalid_token(client: TestClient):
    # delete account with invalid token
    response = client.delete("/api/accounts/", headers={"Authorization": "Bearer invalid_token"})
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Could not validate credentials"

def test_delete_account_not_logged_in(client: TestClient, session: Session):
    # create account in database
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    session.add(Account(**account_hashed))
    session.commit()
    account_id = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first().id
    # delete account without logging in
    response = client.delete("/api/accounts/")
    # check response
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"
    # check database
    account = session.get(Account, account_id)
    assert account is not None
    assert verify_password(ACCOUNT1["password"], account.password_hash)
    assert account.username == ACCOUNT1["username"]

def test_create_account_and_patient(client: TestClient, session: Session):
    # Call combined endpoint
    response = client.post(
        "/api/accounts/account-and-patient/",
        json={"account": ACCOUNT1, "patient": PATIENT1}
    )
    assert response.status_code == 200
    data = response.json()
    print(data)
    # Validate account response
    assert data["username"] == ACCOUNT1["username"]
    assert "password" not in data
    assert "id" not in data
    # Verify in DB
    account = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])) .first()
    assert account is not None
    assert account.patient_id is not None
    patient = session.get(Patient, account.patient_id)
    assert patient is not None
    assert patient.firstname == PATIENT1["firstname"]
    assert patient.lastname == PATIENT1["lastname"]
    assert str(patient.birthday) == PATIENT1["birthday"]


def test_create_account_and_patient_invalid_body(client: TestClient):
    # Missing account and patient fields
    response = client.post("/api/accounts/account-and-patient/", json={})
    assert response.status_code == 422
    data = response.json()
    # Ensure validation errors for both models
    assert any(err["loc"] == ["body", "account"] for err in data["detail"])
    assert any(err["loc"] == ["body", "patient"] for err in data["detail"])

def test_create_account_and_patient_duplicate_username(client: TestClient, session: Session):
    # First creation of account and patient
    client.post(
        "/api/accounts/account-and-patient/",
        json={"account": ACCOUNT1, "patient": PATIENT1}
    )
    # Attempt duplicate username
    response = client.post(
        "/api/accounts/account-and-patient/",
        json={"account": ACCOUNT1, "patient": PATIENT1}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Username already registered"

def test_create_account_and_patient_empty_account_username(client: TestClient):
    return
    response = client.post(
        "/api/accounts/account-and-patient/",
        json={"account": {"username": "", "password": "pwd123"}, "patient": PATIENT1}
    )
    assert response.status_code == 422


def test_create_account_and_patient_empty_account_password(client: TestClient):
    return
    response = client.post(
        "/api/accounts/account-and-patient/",
        json={"account": {"username": "John", "password": ""}, "patient": PATIENT1}
    )
    assert response.status_code == 422


def test_create_account_and_patient_empty_patient_firstname(client: TestClient, session: Session):
    return
    response = client.post(
        "/api/accounts/account-and-patient/",
        json={"account": ACCOUNT1, "patient": {"firstname": "", "lastname": "Smith", "birthday": "1990-05-15"}}
    )
    assert response.status_code == 422

def test_create_account_and_patient_empty_patient_lastname(client: TestClient, session: Session):
    return
    response = client.post(
        "/api/accounts/account-and-patient/",
        json={"account": ACCOUNT1, "patient": {"firstname": "Alice", "lastname": "", "birthday": "1990-05-15"}}
    )
    assert response.status_code == 422

def test_create_account_and_patient_empty_patient_birthday(client: TestClient, session: Session):
    return
    response = client.post(
        "/api/accounts/account-and-patient/",
        json={"account": ACCOUNT1, "patient": {"firstname": "Alice", "lastname": "Smith", "birthday": ""}}
    )
    assert response.status_code == 422