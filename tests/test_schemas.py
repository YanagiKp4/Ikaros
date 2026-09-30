from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from apps.backend.app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
    TaskReminderCreate,
)


TEST_TASK_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_REMIND_AT = datetime(2026, 10, 1, 20, 0, tzinfo=timezone.utc)


def test_reminder_create_accepts_supported_fields():
    reminder = ReminderCreate(
        task_id=TEST_TASK_ID,
        remind_at=TEST_REMIND_AT,
        channel="in_app",
    )

    assert reminder.task_id == TEST_TASK_ID
    assert reminder.remind_at == TEST_REMIND_AT
    assert reminder.channel.value == "in_app"


@pytest.mark.parametrize("status", ["sent", "processing"])
def test_reminder_create_rejects_status(status):
    with pytest.raises(ValidationError):
        ReminderCreate(
            task_id=TEST_TASK_ID,
            remind_at=TEST_REMIND_AT,
            channel="in_app",
            status=status,
        )


def test_task_reminder_create_accepts_supported_fields():
    reminder = TaskReminderCreate(
        remind_at=TEST_REMIND_AT,
        channel="in_app",
    )

    assert reminder.remind_at == TEST_REMIND_AT
    assert reminder.channel.value == "in_app"


@pytest.mark.parametrize("field", ["task_id", "user_id", "status"])
def test_task_reminder_create_rejects_controlled_fields(field):
    with pytest.raises(ValidationError):
        TaskReminderCreate(
            remind_at=TEST_REMIND_AT,
            channel="in_app",
            **{field: TEST_TASK_ID if field != "status" else "pending"},
        )


def test_reminder_update_accepts_cancelled():
    reminder = ReminderUpdate(status="cancelled")

    assert reminder.status == "cancelled"


@pytest.mark.parametrize("status", ["sent", "processing", "failed"])
def test_reminder_update_rejects_internal_statuses(status):
    with pytest.raises(ValidationError):
        ReminderUpdate(status=status)


def test_reminder_update_accepts_remind_at():
    reminder = ReminderUpdate(remind_at=TEST_REMIND_AT)

    assert reminder.remind_at == TEST_REMIND_AT


def test_reminder_update_accepts_channel():
    reminder = ReminderUpdate(channel="email")

    assert reminder.channel.value == "email"


def test_reminder_update_empty_is_valid():
    reminder = ReminderUpdate()

    assert reminder.remind_at is None
    assert reminder.status is None
    assert reminder.channel is None


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (
            ReminderCreate,
            {
                "task_id": TEST_TASK_ID,
                "remind_at": TEST_REMIND_AT,
                "channel": "in_app",
            },
        ),
        (
            ReminderUpdate,
            {},
        ),
        (
            TaskReminderCreate,
            {
                "remind_at": TEST_REMIND_AT,
                "channel": "in_app",
            },
        ),
    ],
)
def test_reminder_schemas_reject_user_id(model, payload):
    with pytest.raises(ValidationError):
        model(**payload, user_id="00000000-0000-0000-0000-000000000002")
