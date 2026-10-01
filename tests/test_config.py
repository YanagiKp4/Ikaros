import os
import subprocess
import sys
from pathlib import Path

import pytest

from apps.backend.app.core import config


@pytest.mark.parametrize(
    "raw_value",
    ["nan", "inf", "+inf", "-inf", "0", "-1", "not-a-number"],
)
def test_positive_float_rejects_invalid_values(monkeypatch, raw_value):
    monkeypatch.setenv("TEST_INTERVAL", raw_value)

    with pytest.raises(RuntimeError, match="TEST_INTERVAL must be a positive number"):
        config._positive_float("TEST_INTERVAL", "10")


def test_api_config_imports_without_worker_key():
    project_root = Path(__file__).resolve().parents[1]
    script = """
import os
from unittest.mock import patch

os.environ["SUPABASE_URL"] = "https://test.supabase.local"
os.environ["SUPABASE_PUBLIC_KEY"] = "test-public-key"
os.environ.pop("SUPABASE_WORKER_KEY", None)

with patch("dotenv.load_dotenv", return_value=False):
    from apps.backend.app.main import app

assert app.title == "IKAROS API"
"""

    environment = os.environ.copy()
    environment.pop("SUPABASE_WORKER_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
