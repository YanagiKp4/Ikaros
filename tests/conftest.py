import os
from unittest.mock import patch


os.environ["SUPABASE_URL"] = "https://test.supabase.local"
os.environ["SUPABASE_PUBLIC_KEY"] = "test-public-key"
os.environ["SUPABASE_WORKER_KEY"] = "test-worker-key"
os.environ["REMINDER_WORKER_INTERVAL_SECONDS"] = "10"
os.environ["REMINDER_WORKER_BATCH_SIZE"] = "10"

import pytest
from fastapi.testclient import TestClient

from tests.fakes.supabase import FakeSupabaseClient


with patch("dotenv.load_dotenv", return_value=False):
    from apps.backend.app.core.security import get_current_user
    from apps.backend.app.main import app


@pytest.fixture
def fake_supabase_client():
    return FakeSupabaseClient()


@pytest.fixture
def user_a(fake_supabase_client):
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "user-a@example.test",
        "full_name": "User A",
        "access_token": "test-token-user-a",
        "client": fake_supabase_client,
    }


@pytest.fixture
def user_b(fake_supabase_client):
    return {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "user-b@example.test",
        "full_name": "User B",
        "access_token": "test-token-user-b",
        "client": fake_supabase_client,
    }


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
