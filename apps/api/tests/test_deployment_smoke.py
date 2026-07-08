import asyncio
import os

import pytest

from main import health, health_db, health_qdrant


def test_app_imports_and_health_endpoint():
    assert health() == {"status": "ok", "service": "api"}


def test_required_environment_variables():
    if not os.getenv("DATABASE_URL") or not os.getenv("QDRANT_URL"):
        pytest.skip("Deployment environment variables are not exported locally")

    assert os.getenv("DATABASE_URL")
    assert os.getenv("QDRANT_URL")


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL is not configured"
)
def test_health_db_endpoint():
    response = health_db()
    assert response["status"] == "ok"
    assert response["db"] == "1"


@pytest.mark.skipif(
    not os.getenv("QDRANT_URL"),
    reason="QDRANT_URL is not configured"
)
def test_health_qdrant_endpoint():
    response = asyncio.run(health_qdrant())
    assert response["status"] == "ok"
    assert "qdrant" in response
