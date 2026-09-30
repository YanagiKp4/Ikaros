from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from apps.backend.app.schemas.task import (
    TaskCreate,
    TaskStatus,
    TaskUpdate,
)
from apps.backend.app.services.task_service import (
    create_task,
    delete_task,
    get_task_by_id,
    get_tasks,
    update_task,
)


TASK_A_ID = "00000000-0000-0000-0000-000000000011"
TASK_B_ID = "00000000-0000-0000-0000-000000000022"
TEST_DUE_DATE = datetime(2026, 10, 2, 20, 0, tzinfo=timezone.utc)


def task_row(task_id, user_id, title):
    return {
        "id": task_id,
        "user_id": user_id,
        "title": title,
        "description": None,
        "status": "pending",
        "priority": "medium",
        "due_date": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


def test_create_task_uses_authenticated_user_and_expected_payload(
    fake_supabase_client,
    user_a,
):
    task = TaskCreate(
        title="Prepare testing",
        description="Task service test",
        status=TaskStatus.pending,
        priority="high",
        due_date=TEST_DUE_DATE,
    )

    created = create_task(fake_supabase_client, task, user_a["id"])

    operation = fake_supabase_client.operations[-1]
    assert operation["table"] == "tasks"
    assert operation["operation"] == "insert"
    assert operation["payload"]["title"] == "Prepare testing"
    assert operation["payload"]["description"] == "Task service test"
    assert operation["payload"]["status"] == "pending"
    assert operation["payload"]["priority"] == "high"
    assert operation["payload"]["due_date"] == "2026-10-02T20:00:00Z"
    assert operation["payload"]["user_id"] == user_a["id"]
    assert created["user_id"] == user_a["id"]
    assert created["title"] == "Prepare testing"


def test_create_task_uses_the_provided_client(fake_supabase_client, user_a):
    assert user_a["client"] is fake_supabase_client

    create_task(
        user_a["client"],
        TaskCreate(title="Provided client"),
        user_a["id"],
    )

    assert fake_supabase_client.operations[-1]["table"] == "tasks"


def test_list_tasks_filters_by_authenticated_user(
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "tasks",
        [
            task_row(TASK_A_ID, user_a["id"], "User A task"),
            task_row(TASK_B_ID, user_b["id"], "User B task"),
        ],
    )

    tasks = get_tasks(fake_supabase_client, user_a["id"])

    assert [task["id"] for task in tasks] == [TASK_A_ID]
    operation = fake_supabase_client.operations[-1]
    assert operation["operation"] == "select"
    assert operation["filters"] == [("eq", "user_id", user_a["id"])]


def test_get_task_by_id_filters_by_task_and_user(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_A_ID, user_a["id"], "User A task")],
    )

    task = get_task_by_id(fake_supabase_client, TASK_A_ID, user_a["id"])

    assert task["id"] == TASK_A_ID
    operation = fake_supabase_client.operations[-1]
    assert operation["filters"] == [
        ("eq", "id", TASK_A_ID),
        ("eq", "user_id", user_a["id"]),
    ]


def test_get_task_by_id_missing_task_returns_404(
    fake_supabase_client,
    user_a,
):
    with pytest.raises(HTTPException) as error:
        get_task_by_id(fake_supabase_client, TASK_A_ID, user_a["id"])

    assert error.value.status_code == 404
    assert error.value.detail == "Task not found"


def test_update_task_uses_expected_payload_and_ownership_filter(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_A_ID, user_a["id"], "Original title")],
    )
    update = TaskUpdate(
        title="Updated title",
        status=TaskStatus.completed,
    )

    updated = update_task(
        fake_supabase_client,
        TASK_A_ID,
        update,
        user_a["id"],
    )

    operation = fake_supabase_client.operations[-1]
    assert operation["operation"] == "update"
    assert operation["payload"] == {
        "title": "Updated title",
        "status": "completed",
    }
    assert operation["filters"] == [
        ("eq", "id", TASK_A_ID),
        ("eq", "user_id", user_a["id"]),
    ]
    assert "user_id" not in operation["payload"]
    assert updated["title"] == "Updated title"
    assert updated["status"] == "completed"


def test_task_update_schema_rejects_user_id():
    with pytest.raises(ValidationError):
        TaskUpdate(user_id="00000000-0000-0000-0000-000000000002")


def test_update_missing_task_returns_404(fake_supabase_client, user_a):
    with pytest.raises(HTTPException) as error:
        update_task(
            fake_supabase_client,
            TASK_A_ID,
            TaskUpdate(title="Missing task"),
            user_a["id"],
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Task not found"


def test_delete_task_uses_task_and_user_filters(
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_A_ID, user_a["id"], "Task to delete")],
    )

    delete_task(fake_supabase_client, TASK_A_ID, user_a["id"])

    operation = fake_supabase_client.operations[-1]
    assert operation["operation"] == "delete"
    assert operation["filters"] == [
        ("eq", "id", TASK_A_ID),
        ("eq", "user_id", user_a["id"]),
    ]
    assert fake_supabase_client.tables["tasks"] == []


def test_delete_missing_task_returns_404(fake_supabase_client, user_a):
    with pytest.raises(HTTPException) as error:
        delete_task(fake_supabase_client, TASK_A_ID, user_a["id"])

    assert error.value.status_code == 404
    assert error.value.detail == "Task not found"


def test_user_cannot_access_modify_or_delete_other_users_task(
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_B_ID, user_b["id"], "User B task")],
    )

    with pytest.raises(HTTPException) as get_error:
        get_task_by_id(fake_supabase_client, TASK_B_ID, user_a["id"])
    assert get_error.value.status_code == 404

    with pytest.raises(HTTPException) as update_error:
        update_task(
            fake_supabase_client,
            TASK_B_ID,
            TaskUpdate(title="Unauthorized update"),
            user_a["id"],
        )
    assert update_error.value.status_code == 404

    with pytest.raises(HTTPException) as delete_error:
        delete_task(fake_supabase_client, TASK_B_ID, user_a["id"])
    assert delete_error.value.status_code == 404

    task_for_user_b = get_task_by_id(
        fake_supabase_client,
        TASK_B_ID,
        user_b["id"],
    )
    assert task_for_user_b["title"] == "User B task"
