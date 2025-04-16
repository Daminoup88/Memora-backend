import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models.model_tables import Question
from app.schemas.schema_question import QuestionRead
from app.dependencies import create_access_token

# Payloads intentionally invalid to trigger errors
invalid_exercises = [
    # Invalid type good body
    ("unknown_type", {
        "question": "Quel est le plus grand pays du monde ?",
        "answer": "Russie"
    }),
    # Exercise missing required keys for 'mcq'
    ("mcq", {
        "question": "Quel est le plus grand océan du monde ?"
        # Missing 'choices' and 'answer'
    }),
    # Exercise with wrong data types
    ("missing_words", {
        "question": 123,  # Should be str
        "answers": "France"  # Should be list
    }),
    # Extra unexpected field
    ("question", {
        "question": "Quelle est la capitale de l'Allemagne ?",
        "answer": "Berlin",
        "extra_field": "error"
    }),
    # Missing words with wrong format (one pipe instead of two)
    ("missing_words", {
        "question": "Paris est la capitale de |France| et Madrid est la capitale de l'Espagne.",
        "answers": ["France", "Madrid"]
    }),
    # Missing words with wrong number of pipes
    ("missing_words", {
        "question": "Paris est la capitale de |France| et |Madrid| est la capitale de l'Espagne.",
        "answers": ["France"]
    }),
    # Match elements with different lengths
    ("match_elements", {
        "column1": ["France", "Espagne"],
        "column2": ["Paris"]
    }),
]

valid_exercises = [
    ("question", {
        "question": "Quelle est la capitale de l'Allemagne ?",
        "answer": "Berlin"
    }),
    ("missing_words", {
        "question": "Paris est la capitale de |France| et |Madrid| est la capitale de l'Espagne.",
        "answers": ["France", "Madrid"]
    }),
    ("mcq", {
        "question": "Quel est le plus grand océan du monde ?",
        "choices": ["Atlantique", "Pacifique", "Indien"],
        "answer": "Pacifique"
    }),
    ("match_elements", {
        "column1": ["France", "Espagne"],
        "column2": ["Paris", "Madrid"]
    }),
    ("chronological_order", {
        "ordered": ["Révolution française", "Première Guerre mondiale", "Seconde Guerre mondiale"]
    })
]

@pytest.mark.parametrize("method, url", [
    ("POST", "/api/questions/"),
    ("GET", "/api/questions/"),
    ("GET", "/api/questions/?question_id=1"),
    ("PUT", "/api/questions/"),
    ("DELETE", "/api/questions/")
])
def test_unauthorized(client: TestClient, method, url, question_payload):
    response = client.request(method, url, json=question_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.parametrize("method, url", [
    ("GET", "/api/questions/?question_id=1"),
    ("PUT", "/api/questions/?question_id=1&manager_id=1"),
    ("DELETE", "/api/questions/?question_id=1")
])
def test_unauthorized_account_manager_action(client: TestClient, method, url, manager_created, manager_created2, question_payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    token2 = manager_created2["token"]
    manager_id2 = manager_created2["manager_id"]
    assert manager_id != manager_id2
    assert token != token2
    create_resp = client.post(f"/api/questions/?manager_id={manager_id}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
    assert create_resp.status_code == 200
    question_id = create_resp.json()["id"]

    if method == "GET" and "question_id" in url:
        url = f"/api/questions/?question_id={question_id}"
    elif method == "PUT":
        url = f"/api/questions/?question_id={question_id}&manager_id={manager_id2}"
    elif method == "DELETE":
        url = f"/api/questions/?question_id={question_id}"

    response = client.request(method, url, json=question_payload, headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 403
    assert response.json()["detail"] in "Not authorized to perform this action"

@pytest.mark.parametrize("method, url", [
    ("POST", "/api/questions/"),
    ("GET", "/api/questions/"),
    ("GET", "/api/questions/?question_id=1"),
    ("PUT", "/api/questions/"),
    ("DELETE", "/api/questions/")
])
def test_fake_token(client: TestClient, method, url, question_payload):
    fake_access_token = create_access_token(data={"sub": 99999})
    response = client.request(method, url, headers={"Authorization": f"Bearer {fake_access_token}"}, json=question_payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"

@pytest.mark.parametrize("method, url", [
    ("POST", "/api/questions/"),
    ("GET", "/api/questions/"),
    ("GET", "/api/questions/?question_id=1"),
    ("PUT", "/api/questions/"),
    ("DELETE", "/api/questions/")
])
def test_invalid_token(client: TestClient, method, url, question_payload):
    invalid_token = "invalid_token"
    response = client.request(method, url, headers={"Authorization": f"Bearer {invalid_token}"}, json=question_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.parametrize("missing_field", ["type", "category", "exercise"])
def test_create_question_missing_fields(client: TestClient, token, missing_field, question_payload):
    payload = question_payload.copy()
    payload.pop(missing_field)
    response = client.post("/api/questions/", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] == missing_field for detail in response.json()["detail"])

@pytest.mark.parametrize("payload", valid_exercises)
def test_create_question_success(client: TestClient, session: Session, manager_created, payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    question_to_create = {
        "category": "general",
        "type": payload[0],
        "exercise": payload[1]
    }
    response = client.post(f"/api/questions/?manager_id={manager_id}", json=question_to_create, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    # Check DB
    question_db = session.exec(select(Question).where(Question.id == data["id"])).first()
    assert question_db is not None
    assert data["id"] is not None
    assert data["type"] == question_to_create["type"] == question_db.type
    assert data["exercise"] == question_to_create["exercise"] == question_db.exercise
    assert data["category"] == question_to_create["category"] == question_db.category

def test_create_question_invalid_body(client: TestClient, token):
    response = client.post("/api/questions/", json={}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    assert any(detail["loc"][-1] in ("type", "category", "exercise") for detail in response.json()["detail"])

@pytest.mark.parametrize("payload", invalid_exercises)
def test_create_question_invalid_exercise(client: TestClient, manager_created, payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    question_to_create = {
        "type": payload[0],
        "category": "general",
        "exercise": payload[1]
    }
    response = client.post(f"/api/questions/?manager_id={manager_id}", json=question_to_create, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400

def test_read_questions(client: TestClient, session: Session, manager_created, question_payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    # Create two questions
    for _ in range(2):
        resp = client.post(f"/api/questions/?manager_id={manager_id}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
    response = client.get("/api/questions/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    # Check DB
    questions_db = session.exec(select(Question).where(Question.created_by == manager_id)).all()
    assert len(questions_db) == 2
    for i, question in enumerate(data):
        assert question["id"] == questions_db[i].id
        assert question["type"] == questions_db[i].type == question_payload["type"]
        assert question["exercise"] == questions_db[i].exercise == question_payload["exercise"]
        assert question["category"] == questions_db[i].category == question_payload["category"]
        assert question["created_by"] == questions_db[i].created_by == manager_id

def test_read_question_by_id(client: TestClient, session: Session, manager_created, question_payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    resp = client.post(f"/api/questions/?manager_id={manager_id}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    question_id = resp.json()["id"]
    response = client.get(f"/api/questions/?question_id={question_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    # Check DB
    question_db = session.exec(select(Question).where(Question.id == question_id)).first()
    assert question_db is not None
    assert data["id"] == question_id == question_db.id
    assert data["type"] == question_payload["type"] == question_db.type
    assert data["exercise"] == question_payload["exercise"] == question_db.exercise
    assert data["category"] == question_payload["category"] == question_db.category

def test_read_question_by_id_not_found(client: TestClient, manager_created):
    token = manager_created["token"]
    response = client.get("/api/questions/?question_id=99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Question not found"

def test_update_question_success(client: TestClient, session: Session, manager_created, question_payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    resp = client.post(f"/api/questions/?manager_id={manager_id}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    question_id = resp.json()["id"]
    update_payload = question_payload.copy()
    update_payload["exercise"] = {"question": "Nouvelle question?", "answer": "Réponse"}
    update_payload["id"] = question_id
    response = client.put(f"/api/questions/?question_id={question_id}&manager_id={manager_id}", json=update_payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    # Check DB
    question_db = session.exec(select(Question).where(Question.id == question_id)).first()
    assert question_db is not None
    assert data["id"] == question_id == question_db.id
    assert data["type"] == question_payload["type"] == question_db.type
    assert data["category"] == question_payload["category"] == question_db.category
    assert data["exercise"] == update_payload["exercise"] == question_db.exercise

def test_update_question_not_found(client: TestClient, manager_created, question_payload):
    token = manager_created["token"]
    update_payload = question_payload.copy()
    update_payload["id"] = 99999
    response = client.put("/api/questions/?question_id=99999", json=update_payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Question not found"

def test_update_question_invalid_body(client: TestClient, manager_created, question_payload):
    token = manager_created["token"]
    # First create a question to update
    resp = client.post(f"/api/questions/?manager_id={manager_created['manager_id']}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    print(resp.json())
    question_id = resp.json()["id"]
    response = client.put(f"/api/questions/?question_id={question_id}&manager_id={manager_created['manager_id']}", json={}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422

def test_update_question_no_manager_id(client: TestClient, session: Session, manager_created, question_payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    resp = client.post(f"/api/questions/?manager_id={manager_id}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    question_id = resp.json()["id"]
    update_payload = question_payload.copy()
    update_payload["exercise"] = {"question": "Nouvelle question?", "answer": "Réponse"}
    update_payload["id"] = question_id
    response = client.put(f"/api/questions/?question_id={question_id}", json=update_payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422
    # Check DB
    question_db = session.exec(select(Question).where(Question.id == question_id)).first()
    assert question_db is not None
    assert question_db.exercise == question_payload["exercise"]
    assert question_db.type == question_payload["type"]
    assert question_db.category == question_payload["category"]

def test_update_question_no_question_id(client: TestClient, session: Session, manager_created, question_payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    resp = client.post(f"/api/questions/?manager_id={manager_id}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    question_id = resp.json()["id"]
    update_payload = question_payload.copy()
    update_payload["exercise"] = {"question": "Nouvelle question?", "answer": "Réponse"}
    update_payload["id"] = question_id
    response = client.put(f"/api/questions/?manager_id={manager_id}", json=update_payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "question_id query parameter required"
    # Check DB
    question_db = session.exec(select(Question).where(Question.id == question_id)).first()
    assert question_db is not None
    assert question_db.exercise == question_payload["exercise"]
    assert question_db.type == question_payload["type"]
    assert question_db.category == question_payload["category"]

def test_delete_question_success(client: TestClient, session: Session, manager_created, question_payload):
    token = manager_created["token"]
    manager_id = manager_created["manager_id"]
    resp = client.post(f"/api/questions/?manager_id={manager_id}", json=question_payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    question_id = resp.json()["id"]
    response = client.delete(f"/api/questions/?question_id={question_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"detail": "Question deleted successfully"}
    # Check DB
    question_db = session.exec(select(Question).where(Question.id == question_id)).first()
    assert question_db is None
    # Try to delete again
    response2 = client.delete(f"/api/questions/?question_id={question_id}", headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 404
    assert response2.json()["detail"] == "Question not found"

def test_delete_question_not_found(client: TestClient, manager_created):
    token = manager_created["token"]
    response = client.delete("/api/questions/?question_id=99999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Question not found"