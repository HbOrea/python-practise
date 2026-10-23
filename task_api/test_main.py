import pytest
from fastapi.testclient import TestClient
from main import app, reset_store

@pytest.fixture
def client():
    reset_store()
    with TestClient(app) as test_client:
        yield test_client

def test_create_and_list(client):
    response = client.post("/tasks", json={"title": "学习 Python"})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "title": "学习 Python", "done": False}
    assert len(client.get("/tasks").json()) == 1

def test_validation_and_missing(client):
    assert client.post("/tasks", json={"title": "  "}).status_code == 422
    assert client.get("/tasks/999").status_code == 404

# def test_complete_and_analyze(client):
#     task = client.post("/tasks", json={"title": "整理材料"}).json()
#     task_id = task["id"]
#     result = client.patch(f"/tasks/{task_id}/done")
#     assert result.json()["done"] is True
#     analysis = client.post(f"/tasks/{task_id}/analyze")
#     assert analysis.status_code == 200
#     assert analysis.json()["title"] == "整理材料"
