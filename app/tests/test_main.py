from fastapi.testclient import TestClient
from app.main import app

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_read_random(client: TestClient):
    response = client.get("/random")
    assert response.status_code == 200
    assert "random" in response.json()
    assert 1 <= response.json()["random"] <= 100