from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.model_tables import Account, Patient
from app.dependencies import get_password_hash, create_access_token, verify_password
import datetime

PATIENT1 = {"firstname": "John", "lastname": "Doe", "birthday": "2000-01-01T00:00:00"}
ACCOUNT1 = {"username": "patientowner", "password": "pwd123"}

def _create_account_and_get_token(client: TestClient, session: Session):
    # Create account directly in DB
    account_hashed = ACCOUNT1.copy()
    account_hashed["password_hash"] = get_password_hash(account_hashed.pop("password"))
    db_account = Account(**account_hashed)
    session.add(db_account)
    session.commit()
    session.refresh(db_account)
    # Retrieve token via API
    response = client.post("/api/auth/token", data={"username": ACCOUNT1["username"], "password": ACCOUNT1["password"]})
    if response.status_code == 200:
        return response.json()["access_token"]
    return create_access_token(data={"sub": db_account.id})

def _test_unauthorized(client: TestClient, method: str, url: str, json: dict = None):
    # Test unauthorized access (missing token)
    response = client.request(method, url, json=json)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def _test_invalid_token(client: TestClient, method: str, url: str, token: str, json: dict = None):
    # Test access with an invalid token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.request(method, url, headers=headers, json=json)
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"

def _test_not_found(client: TestClient, method: str, url: str, token: str, json: dict = None):
    # Test access when the resource is not found
    headers = {"Authorization": f"Bearer {token}"}
    response = client.request(method, url, headers=headers, json=json)
    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"

def test_create_patient(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    response = client.post("/api/patients/", json=PATIENT1, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    # Check DB
    account = session.exec(select(Account).where(Account.username == ACCOUNT1["username"])).first()
    patient = session.exec(select(Patient).where(Patient.firstname == PATIENT1["firstname"])).first()
    assert account is not None
    assert patient is not None
    assert account.patient_id == patient.id

def test_create_patient_already_registered(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    # Create patient once
    client.post("/api/patients/", json=PATIENT1, headers={"Authorization": f"Bearer {token}"})
    # Try to create again
    response = client.post("/api/patients/", json=PATIENT1, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Patient already registered"

def test_create_patient_invalid_data(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    # Invalid date format
    invalid_patient = PATIENT1.copy()
    invalid_patient["birthday"] = "invalid_date"
    response = client.post("/api/patients/", json=invalid_patient, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"] == ["body", "birthday"] and data["detail"][0]["input"] == "invalid_date"
    # Missing required field
    invalid_patient = PATIENT1.copy()
    invalid_patient.pop("firstname")
    response = client.post("/api/patients/", json=invalid_patient, headers={"Authorization": f"Bearer {token}"})
    data = response.json()
    assert response.status_code == 422
    assert data["detail"][0]["loc"] == ["body", "firstname"] and data["detail"][0]["msg"] == "Field required"

def test_create_patient_unauthorized(client: TestClient):
    _test_unauthorized(client, "POST", "/api/patients/", json=PATIENT1)

def test_create_patient_invalid_token(client: TestClient):
    fake_access_token = create_access_token(data={"sub": 99999})
    _test_invalid_token(client, "POST", "/api/patients/", token=fake_access_token, json=PATIENT1)

def test_read_patient(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    # Create patient
    client.post("/api/patients/", json=PATIENT1, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/api/patients/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["firstname"] == PATIENT1["firstname"]
    assert data["lastname"] == PATIENT1["lastname"]

def test_read_patient_not_found(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    _test_not_found(client, "GET", "/api/patients/", token=token)

def test_read_patient_unauthorized(client: TestClient):
    _test_unauthorized(client, "GET", "/api/patients/")

def test_read_patient_invalid_token(client: TestClient):
    fake_access_token = create_access_token(data={"sub": 99999})
    _test_invalid_token(client, "GET", "/api/patients/", token=fake_access_token)

def test_update_patient(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    # Create patient
    client.post("/api/patients/", json=PATIENT1, headers={"Authorization": f"Bearer {token}"})
    # Update patient
    updated_data = {"firstname": "Johnny", "lastname": "Updated", "birthday": "2000-01-01"}
    response = client.put("/api/patients/", json=updated_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["firstname"] == "Johnny"
    assert data["lastname"] == "Updated"

def test_update_patient_invalid_data(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    # Create patient
    client.post("/api/patients/", json=PATIENT1, headers={"Authorization": f"Bearer {token}"})
    # Invalid date format
    invalid_data = {"firstname": "Johnny", "lastname": "Updated", "birthday": "invalid_date"}
    response = client.put("/api/patients/", json=invalid_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"] == ["body", "birthday"] and data["detail"][0]["input"] == "invalid_date"
    # Missing required field
    invalid_data = {"lastname": "Updated", "birthday": "2000-01-01"}
    response = client.put("/api/patients/", json=invalid_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"] == ["body", "firstname"] and data["detail"][0]["msg"] == "Field required"

def test_update_patient_not_found(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    updated_data = {"firstname": "Johnny", "lastname": "Updated", "birthday": "2000-01-01"}
    _test_not_found(client, "PUT", "/api/patients/", token=token, json=updated_data)

def test_update_patient_unauthorized(client: TestClient):
    updated_data = {"firstname": "Johnny", "lastname": "Updated", "birthday": "2000-01-01"}
    _test_unauthorized(client, "PUT", "/api/patients/", json=updated_data)

def test_update_patient_invalid_token(client: TestClient):
    fake_access_token = create_access_token(data={"sub": 99999})
    updated_data = {"firstname": "Johnny", "lastname": "Updated", "birthday": "2000-01-01"}
    _test_invalid_token(client, "PUT", "/api/patients/", token=fake_access_token, json=updated_data)

def test_delete_patient(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    # Create patient
    client.post("/api/patients/", json=PATIENT1, headers={"Authorization": f"Bearer {token}"})
    # Delete patient
    response = client.delete("/api/patients/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "Patient deleted successfully"}
    # Check DB
    patient = session.exec(select(Patient).where(Patient.firstname == PATIENT1["firstname"])).first()
    assert patient is None

def test_delete_patient_not_found(client: TestClient, session: Session):
    token = _create_account_and_get_token(client, session)
    _test_not_found(client, "DELETE", "/api/patients/", token=token)

def test_delete_patient_unauthorized(client: TestClient):
    _test_unauthorized(client, "DELETE", "/api/patients/")

def test_delete_patient_invalid_token(client: TestClient):
    fake_access_token = create_access_token(data={"sub": 99999})
    _test_invalid_token(client, "DELETE", "/api/patients/", token=fake_access_token)