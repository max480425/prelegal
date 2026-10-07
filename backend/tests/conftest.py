"""Shared test fixtures.

Environment is configured *before* any `backend.*` import so that the
lru_cached settings pick up the temporary database and document directories.
"""

import atexit
import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Temporary, isolated state for the whole test session (set before importing
# backend.main, whose module-level `get_settings()` call caches these values).
_TEST_DIR = tempfile.mkdtemp(prefix="prelegal_test_")
atexit.register(shutil.rmtree, _TEST_DIR, ignore_errors=True)

_REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ["DATABASE_PATH"] = str(Path(_TEST_DIR) / "test.db")
os.environ["DOCUMENTS_DIR"] = str(Path(_TEST_DIR) / "documents")
os.environ["TEMPLATES_DIR"] = str(_REPO_ROOT / "templates")
os.environ["JWT_SECRET"] = "test-secret-at-least-32-bytes-long!!"
os.environ["JWT_EXPIRE_MINUTES"] = "60"
# Override the repo .env key so tests can never call the real OpenRouter API
# (the LLM seam is monkeypatched in chat tests; this is belt-and-braces).
os.environ["OPENROUTER_API_KEY"] = "sk-test-offline"

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from backend.utils.db import clear_users, init_db  # noqa: E402

# Create the schema once for the whole session (pythonpath comes from
# pytest.ini, so imports work regardless of invocation style).
init_db()


@pytest.fixture()
def client():
    """TestClient with a clean users table for each test."""
    clear_users()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def registered_user(client):
    """Sign up a user and return their credentials."""
    credentials = {"email": "tester@example.com", "password": "s3cure-pass"}
    response = client.post("/api/auth/signup", json=credentials)
    assert response.status_code == 201, response.text
    return credentials
