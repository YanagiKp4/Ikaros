import math
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _positive_float(name: str, default: str) -> float:
    raw_value = os.getenv(name, default)
    try:
        value = float(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a positive number") from error

    if not math.isfinite(value) or value <= 0:
        raise RuntimeError(f"{name} must be a positive number")

    return value


def _positive_int(name: str, default: str) -> int:
    raw_value = os.getenv(name, default)
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a positive integer") from error

    if value <= 0:
        raise RuntimeError(f"{name} must be a positive integer")

    return value


SUPABASE_URL = _require_env("SUPABASE_URL")
SUPABASE_PUBLIC_KEY = _require_env("SUPABASE_PUBLIC_KEY")
SUPABASE_WORKER_KEY = os.getenv("SUPABASE_WORKER_KEY")

REMINDER_WORKER_INTERVAL_SECONDS = _positive_float(
    "REMINDER_WORKER_INTERVAL_SECONDS",
    "10"
)
REMINDER_WORKER_BATCH_SIZE = _positive_int(
    "REMINDER_WORKER_BATCH_SIZE",
    "10"
)
