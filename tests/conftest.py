import os
from pathlib import Path

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("DATABASE_URL", "sqlite:///./phase3_test.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"Authorization": "Bearer test-token", "X-Actor": "pytest"}
AUTH_ONLY = {"Authorization": "Bearer test-token"}


@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    yield
    Path("phase3_test.db").unlink(missing_ok=True)


@pytest.fixture()
def client():
    c = TestClient(app)
    c.post("/test/reset", headers=HEADERS)
    yield c
    c.post("/test/reset", headers=HEADERS)
