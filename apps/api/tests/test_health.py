from fastapi.testclient import TestClient

from repopilot_api import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
