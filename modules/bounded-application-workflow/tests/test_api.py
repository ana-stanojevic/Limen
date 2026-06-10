from fastapi.testclient import TestClient

from app.api.main import app
from tests.fixture_helpers import load_fixture

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_workflow():
    fixture = load_fixture("strong_match.json")
    response = client.post(
        "/workflow/run",
        json={
            "user_profile": fixture["user_profile"],
            "job_description": fixture["job_description"],
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"]["decision"] == fixture["expected_decision"]


def test_run_workflow_rejects_invalid_payload():
    assert client.post("/workflow/run", json={}).status_code == 422
