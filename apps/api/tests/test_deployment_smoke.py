import os

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_app_imports_and_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}


def test_required_environment_variables():
    assert os.getenv("DATABASE_URL"), "DATABASE_URL must be set for deployment"
    assert os.getenv("QDRANT_URL"), "QDRANT_URL must be set for deployment"


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL is not configured"
)
def test_health_db_endpoint(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["db"] == "1"


@pytest.mark.skipif(
    not os.getenv("QDRANT_URL"),
    reason="QDRANT_URL is not configured"
)
def test_health_qdrant_endpoint(client):
    response = client.get("/health/qdrant")
    assert response.status_code == 200
    json_body = response.json()
    assert json_body["status"] == "ok"
    assert "qdrant" in json_body
