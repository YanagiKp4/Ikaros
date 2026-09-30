from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from apps.backend.app.schemas.reminder import (
    ReminderCreate,
    ReminderUpdate,
)
from apps.backend.app.services.reminder_service import (
    create_reminder,
    delete_reminder,
    get_reminder_by_id,
    get_reminders,
    update_reminder,
)


TASK_A_ID = "00000000-0000-0000-0000-000000000011"
TASK_B_ID = "00000000-0000-0000-0000-000000000022"
REMINDER_A_ID = "00000000-0000-0000-0000-000000000111"
REMINDER_B_ID = "00000000-0000-0000-0000-000000000222"
TEST_REMIND_AT = datetime(2026, 10, 1, 20, 0, tzinfo=timezone.utc)
UPDATED_REMIND_AT = datetime(2026, 10, 2, 21, 30, tzinfo=timezone.utc)


def task_row(task_id, user_id):
    return {
        "id": task_id,
        "user_id": user_id,
    }


def reminder_row(reminder_id, task_id, user_id, status="pending"):
    return {
        "id": reminder_id,
        "task_id": task_id,
        "user_id": user_id,
        "remind_at": "2026-10-01T20:00:00+00:00",
        "status": status,
        "channel": "in_app",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


def test_create_reminder_forces_pending_and_uses_authenticated_user(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_A_ID, user_a["id"])],
    )
    reminder = ReminderCreate(
        task_id=UUID(TASK_A_ID),
        remind_at=TEST_REMIND_AT,
        channel="in_app",
    )

    created = create_reminder(
        user_a["client"],
        reminder,
        user_a["id"],
    )

    operation = fake_supabase_client.operations[-1]
    assert operation["table"] == "reminders"
    assert operation["operation"] == "insert"
    assert operation["payload"] == {
        "task_id": TASK_A_ID,
        "remind_at": "2026-10-01T20:00:00Z",
        "channel": "in_app",
        "user_id": user_a["id"],
        "status": "pending",
    }
    assert created["task_id"] == TASK_A_ID
    assert created["user_id"] == user_a["id"]
    assert created["status"] == "pending"
    assert created["channel"] == "in_app"


def test_create_reminder_validates_task_ownership_before_insert(
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_B_ID, user_b["id"])],
    )
    reminder = ReminderCreate(
        task_id=UUID(TASK_B_ID),
        remind_at=TEST_REMIND_AT,
        channel="in_app",
    )

    with pytest.raises(HTTPException) as error:
        create_reminder(user_a["client"], reminder, user_a["id"])

    assert error.value.status_code == 404
    assert error.value.detail == "Task not found"
    assert not any(
        operation["operation"] == "insert"
        for operation in fake_supabase_client.operations
    )


@pytest.mark.parametrize("status", ["sent", "processing", "failed"])
def test_create_reminder_does_not_accept_arbitrary_status(status):
    with pytest.raises(ValidationError):
        ReminderCreate(
            task_id=UUID(TASK_A_ID),
            remind_at=TEST_REMIND_AT,
            channel="in_app",
            status=status,
        )


def test_list_reminders_filters_by_authenticated_user(
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "reminders",
        [
            reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"]),
            reminder_row(REMINDER_B_ID, TASK_B_ID, user_b["id"]),
        ],
    )

    reminders = get_reminders(fake_supabase_client, user_a["id"])

    assert [reminder["id"] for reminder in reminders] == [REMINDER_A_ID]
    operation = fake_supabase_client.operations[-1]
    assert operation["filters"] == [
        ("eq", "user_id", user_a["id"]),
    ]


def test_get_reminder_by_id_filters_by_reminder_and_user(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"])],
    )

    reminder = get_reminder_by_id(
        fake_supabase_client,
        REMINDER_A_ID,
        user_a["id"],
    )

    assert reminder["id"] == REMINDER_A_ID
    operation = fake_supabase_client.operations[-1]
    assert operation["filters"] == [
        ("eq", "id", REMINDER_A_ID),
        ("eq", "user_id", user_a["id"]),
    ]


def test_get_missing_reminder_returns_404(fake_supabase_client, user_a):
    with pytest.raises(HTTPException) as error:
        get_reminder_by_id(
            fake_supabase_client,
            REMINDER_A_ID,
            user_a["id"],
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Recordatorio no encontrado"


def test_update_pending_reminder_updates_fields_and_filters_status(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"])],
    )
    update = ReminderUpdate(
        remind_at=UPDATED_REMIND_AT,
        channel="email",
    )

    updated = update_reminder(
        fake_supabase_client,
        REMINDER_A_ID,
        update,
        user_a["id"],
    )

    operation = fake_supabase_client.operations[-1]
    assert operation["operation"] == "update"
    assert operation["payload"] == {
        "remind_at": "2026-10-02T21:30:00Z",
        "channel": "email",
    }
    assert operation["filters"] == [
        ("eq", "id", REMINDER_A_ID),
        ("eq", "user_id", user_a["id"]),
        ("eq", "status", "pending"),
    ]
    assert "user_id" not in operation["payload"]
    assert updated["remind_at"] == "2026-10-02T21:30:00Z"
    assert updated["channel"] == "email"


def test_update_reminder_rejects_user_id():
    with pytest.raises(ValidationError):
        ReminderUpdate(user_id=user_a_id_placeholder())


def user_a_id_placeholder():
    return "00000000-0000-0000-0000-000000000001"


@pytest.mark.parametrize("status", ["sent", "processing", "failed"])
def test_update_reminder_rejects_internal_statuses(status):
    with pytest.raises(ValidationError):
        ReminderUpdate(status=status)


def test_update_missing_reminder_returns_404(fake_supabase_client, user_a):
    with pytest.raises(HTTPException) as error:
        update_reminder(
            fake_supabase_client,
            REMINDER_A_ID,
            ReminderUpdate(channel="email"),
            user_a["id"],
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Recordatorio no encontrado"


def test_delete_reminder_filters_by_reminder_and_user(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"])],
    )

    delete_reminder(
        fake_supabase_client,
        REMINDER_A_ID,
        user_a["id"],
    )

    operation = fake_supabase_client.operations[-1]
    assert operation["operation"] == "delete"
    assert operation["filters"] == [
        ("eq", "id", REMINDER_A_ID),
        ("eq", "user_id", user_a["id"]),
    ]
    assert fake_supabase_client.tables["reminders"] == []


def test_delete_missing_reminder_returns_404(fake_supabase_client, user_a):
    with pytest.raises(HTTPException) as error:
        delete_reminder(
            fake_supabase_client,
            REMINDER_A_ID,
            user_a["id"],
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Recordatorio no encontrado"


def test_user_cannot_access_modify_or_delete_other_users_reminder(
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_B_ID, TASK_B_ID, user_b["id"])],
    )

    reminders = get_reminders(fake_supabase_client, user_a["id"])
    assert reminders == []

    with pytest.raises(HTTPException) as update_error:
        update_reminder(
            fake_supabase_client,
            REMINDER_B_ID,
            ReminderUpdate(channel="email"),
            user_a["id"],
        )
    assert update_error.value.status_code == 404

    with pytest.raises(HTTPException) as delete_error:
        delete_reminder(
            fake_supabase_client,
            REMINDER_B_ID,
            user_a["id"],
        )
    assert delete_error.value.status_code == 404

    reminder_for_user_b = get_reminder_by_id(
        fake_supabase_client,
        REMINDER_B_ID,
        user_b["id"],
    )
    assert reminder_for_user_b["user_id"] == user_b["id"]


def test_create_reminder_uses_provided_authenticated_client(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_A_ID, user_a["id"])],
    )
    create_reminder(
        user_a["client"],
        ReminderCreate(
            task_id=UUID(TASK_A_ID),
            remind_at=TEST_REMIND_AT,
            channel="in_app",
        ),
        user_a["id"],
    )

    assert user_a["client"] is fake_supabase_client
    assert fake_supabase_client.operations[-1]["table"] == "reminders"
