import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.model_tables import Manager
from app.models.model_tables import Account
from app.schemas.schema_manager import ManagerRead
from app.dependencies import create_access_token, get_password_hash

@pytest.mark.parametrize("method, url", [
    ("POST", "/api/managers/"),
    ("GET", "/api/managers/"),
    ("GET", "/api/managers/1"),
    ("PUT", "/api/managers/1"),
    ("DELETE", "/api/managers/1"),
])
def test_unauthorized(client: TestClient, method, url, manager1):
    response = client.request(method, url, json=manager1)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.parametrize("method, url", [
    ("POST", "/api/managers/"),
    ("GET", "/api/managers/"),
    ("GET", "/api/managers/1"),
    ("PUT", "/api/managers/1"),
    ("DELETE", "/api/managers/1"),
])
def test_invalid_token(client: TestClient, method, url, manager1):
    fake_access_token = create_access_token(data={"sub": 99999})
    response = client.request(method, url, headers={"Authorization": f"Bearer {fake_access_token}"}, json=manager1)
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"

@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_unauthorized_account_manager_action(client: TestClient, session: Session, method, token, manager1, account2):
    account2_hashed = account2.copy()
    account2_hashed["password_hash"] = get_password_hash(account2_hashed.pop("password"))
    account2_obj = Account(**account2_hashed)
    session.add(account2_obj)
    session.commit()
    session.refresh(account2_obj)
    account2_token = create_access_token(data={"sub": account2_obj.id})
    assert account2_token != token
    response = client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {account2_token}"})
    assert response.status_code == 200
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    manager_id = manager.id

    # Attempt actions with an unrelated account
    url = f"/api/managers/{manager_id}"
    response = client.request(method, url, headers={"Authorization": f"Bearer {token}"}, json=manager1 if method == "PUT" else None)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to perform this action"

def test_create_manager(client: TestClient, session: Session, token, manager1):
    response = client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    # Validate response schema (dict)
    assert response.json() == {}
    # Check DB
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    assert manager is not None
    assert manager.firstname == manager1["firstname"]
    assert manager.lastname == manager1["lastname"]
    assert manager.relationship == manager1["relationship"]
    assert manager.email == manager1["email"]

def test_create_manager_already_used_email(client: TestClient, session: Session, token, manager1):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    response = client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already used"

def test_create_manager_invalid_body(client: TestClient, token):
    response = client.post("/api/managers/", json={}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] == "email" for detail in response.json()["detail"])
    assert any(detail["loc"][-1] == "firstname" for detail in response.json()["detail"])
    assert any(detail["loc"][-1] == "lastname" for detail in response.json()["detail"])
    assert any(detail["loc"][-1] == "relationship" for detail in response.json()["detail"])

@pytest.mark.parametrize("missing_field", ["email", "firstname", "lastname", "relationship"])
def test_create_manager_missing_required_fields(client: TestClient, token, manager1, missing_field):
    incomplete_manager = manager1.copy()
    incomplete_manager.pop(missing_field, None)
    response = client.post("/api/managers/", json=incomplete_manager, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] == missing_field for detail in response.json()["detail"])

# def test_create_manager_invalid_email_format(client: TestClient, token, manager1):
#     invalid_manager = manager1.copy()
#     invalid_manager["email"] = "invalid_email"
#     response = client.post("/api/managers/", json=invalid_manager, headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 422
#     assert any(detail["loc"][-1] == "email" for detail in response.json()["detail"])

def test_read_managers(client: TestClient, session: Session, token, account1, manager1, manager2):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    client.post("/api/managers/", json=manager2, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/api/managers/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    managers_read = [ManagerRead(**mgr_data) for mgr_data in data]
    assert all(isinstance(mgr, ManagerRead) for mgr in managers_read)
    assert manager1["firstname"] in [mgr.firstname for mgr in managers_read]
    assert manager2["firstname"] in [mgr.firstname for mgr in managers_read]
    assert manager1["lastname"] in [mgr.lastname for mgr in managers_read]
    assert manager2["lastname"] in [mgr.lastname for mgr in managers_read]
    assert manager1["relationship"] in [mgr.relationship for mgr in managers_read]
    assert manager2["relationship"] in [mgr.relationship for mgr in managers_read]
    
    # Check DB
    managers = session.exec(select(Manager).where(Manager.email.in_([manager1["email"], manager2["email"]]))).all()
    account = session.exec(select(Account).where(Account.username == account1["username"])).first()
    assert len(managers) == 2
    assert all(mgr.firstname in [manager1["firstname"], manager2["firstname"]] for mgr in managers)
    assert all(mgr.lastname in [manager1["lastname"], manager2["lastname"]] for mgr in managers)
    assert all(mgr.relationship in [manager1["relationship"], manager2["relationship"]] for mgr in managers)
    assert all(mgr.account_id == account.id for mgr in managers)

def test_read_manager_by_id(client: TestClient, session: Session, token, account1, manager1):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    manager_id = manager.id
    response = client.get(f"/api/managers/{manager_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == manager_id
    assert data["firstname"] == manager1["firstname"]
    assert data["lastname"] == manager1["lastname"]
    assert ManagerRead(**data)

    # Check DB
    manager_from_db = session.get(Manager, manager_id)
    assert manager_from_db is not None
    assert manager_from_db.firstname == manager1["firstname"]
    assert manager_from_db.lastname == manager1["lastname"]
    assert manager_from_db.relationship == manager1["relationship"]
    assert manager_from_db.email == manager1["email"]
    assert manager_from_db.account_id == session.exec(select(Account).where(Account.username == account1["username"])).first().id

def test_read_manager_by_id_not_found(client: TestClient, token):
    manager_id = 99999
    response = client.get(f"/api/managers/{manager_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Manager not found"

def test_read_manager_by_id_invalid_id_format(client: TestClient, token):
    response = client.get("/api/managers/invalid_id", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] == "manager_id" for detail in response.json()["detail"])

def test_read_managers_empty(client: TestClient, token):
    response = client.get("/api/managers/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "No managers found"

def test_update_manager(client: TestClient, session: Session, token, manager1, manager2):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    manager_id = manager.id
    response = client.put(f"/api/managers/{manager_id}", json=manager2, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["firstname"] == manager2["firstname"]
    assert data["lastname"] == manager2["lastname"]
    assert data["relationship"] == manager2["relationship"]
    session.refresh(manager)
    assert manager.email == manager2["email"]
    assert manager.firstname == manager2["firstname"]
    assert manager.lastname == manager2["lastname"]

@pytest.mark.parametrize("missing_field", ["email", "firstname", "lastname", "relationship"])
def test_update_manager_missing_required_fields(client: TestClient, session: Session, token, manager1, missing_field):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    manager_id = manager.id
    update_data = manager1.copy()
    update_data.pop(missing_field, None)
    response = client.put(f"/api/managers/{manager_id}", json=update_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] == missing_field for detail in response.json()["detail"])

# def test_update_manager_invalid_email_format(client: TestClient, session: Session, token, manager1):
#     client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
#     manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
#     manager_id = manager.id
#     update_data = manager1.copy()
#     update_data["email"] = "invalid_email"
#     response = client.put(f"/api/managers/{manager_id}", json=update_data, headers={"Authorization": f"Bearer {token}"})
#     assert response.status_code == 422
#     assert any(detail["loc"][-1] == "email" for detail in response.json()["detail"])

def test_update_manager_not_found(client: TestClient, token, manager1):
    manager_id = 99999
    response = client.put(f"/api/managers/{manager_id}", json=manager1, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Manager not found"

def test_update_manager_invalid_id_format(client: TestClient, token, manager1):
    response = client.put("/api/managers/invalid_id", json=manager1, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] == "manager_id" for detail in response.json()["detail"])

def test_update_manager_already_used_email(client: TestClient, session: Session, token, manager1, manager2):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    client.post("/api/managers/", json=manager2, headers={"Authorization": f"Bearer {token}"})
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    manager_id = manager.id
    response = client.put(f"/api/managers/{manager_id}", json=manager2, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already used"

def test_delete_manager(client: TestClient, session: Session, token, manager1):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    manager_id = manager.id
    response = client.delete(f"/api/managers/{manager_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "Manager deleted successfully"}
    manager_deleted = session.get(Manager, manager_id)
    assert manager_deleted is None

def test_delete_manager_already_deleted(client: TestClient, session: Session, token, manager1):
    client.post("/api/managers/", json=manager1, headers={"Authorization": f"Bearer {token}"})
    manager = session.exec(select(Manager).where(Manager.email == manager1["email"])).first()
    manager_id = manager.id
    response = client.delete(f"/api/managers/{manager_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    response = client.delete(f"/api/managers/{manager_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Manager not found"

def test_delete_manager_not_found(client: TestClient, token):
    manager_id = 99999
    response = client.delete(f"/api/managers/{manager_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Manager not found"

def test_delete_manager_invalid_id_format(client: TestClient, token):
    response = client.delete("/api/managers/invalid_id", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] == "manager_id" for detail in response.json()["detail"])