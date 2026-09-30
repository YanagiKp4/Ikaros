from unittest.mock import Mock

from apps.backend.app.core.security import get_current_user
from apps.backend.app.main import app


TASK_A_ID = "00000000-0000-0000-0000-000000000011"
TASK_B_ID = "00000000-0000-0000-0000-000000000022"
REMINDER_A_ID = "00000000-0000-0000-0000-000000000111"
REMINDER_B_ID = "00000000-0000-0000-0000-000000000222"


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


def reminder_payload(task_id=TASK_A_ID):
    return {
        "task_id": task_id,
        "remind_at": "2026-10-01T20:00:00Z",
        "channel": "in_app",
    }


def nested_reminder_payload():
    return {
        "remind_at": "2026-10-01T20:00:00Z",
        "channel": "in_app",
    }


def test_create_reminder_returns_201_pending_for_owned_task(
    client,
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_A_ID, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post("/reminders", json=reminder_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["task_id"] == TASK_A_ID
    assert body["user_id"] == user_a["id"]
    assert body["status"] == "pending"
    assert body["channel"] == "in_app"


def test_create_reminder_rejects_task_owned_by_another_user(
    client,
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_B_ID, user_b["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post(
        "/reminders",
        json=reminder_payload(TASK_B_ID),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
    assert not any(
        operation["operation"] == "insert"
        for operation in fake_supabase_client.operations
    )


def test_create_nested_reminder_returns_201_with_route_task_id(
    client,
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_A_ID, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post(
        f"/tasks/{TASK_A_ID}/reminders",
        json=nested_reminder_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["task_id"] == TASK_A_ID
    assert body["user_id"] == user_a["id"]
    assert body["status"] == "pending"


def test_create_nested_reminder_rejects_task_owned_by_another_user(
    client,
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "tasks",
        [task_row(TASK_B_ID, user_b["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post(
        f"/tasks/{TASK_B_ID}/reminders",
        json=nested_reminder_payload(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_list_reminders_returns_only_authenticated_users_reminders(
    client,
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
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.get("/reminders")

    assert response.status_code == 200
    body = response.json()
    assert [reminder["id"] for reminder in body] == [REMINDER_A_ID]


def test_get_reminder_returns_200_for_owned_reminder(
    client,
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.get(f"/reminders/{REMINDER_A_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == REMINDER_A_ID


def test_get_reminder_rejects_other_user_and_missing_reminder(
    client,
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_B_ID, TASK_B_ID, user_b["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    other_user_response = client.get(f"/reminders/{REMINDER_B_ID}")
    missing_response = client.get(
        "/reminders/00000000-0000-0000-0000-000000000999"
    )

    assert other_user_response.status_code == 404
    assert missing_response.status_code == 404


def test_update_pending_reminder_returns_200(
    client,
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.put(
        f"/reminders/{REMINDER_A_ID}",
        json={
            "remind_at": "2026-10-02T21:30:00Z",
            "channel": "email",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["remind_at"] == "2026-10-02T21:30:00Z"
    assert body["channel"] == "email"
    assert body["status"] == "pending"


def test_update_reminder_rejects_internal_statuses(
    client,
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    for internal_status in ("sent", "processing", "failed"):
        response = client.put(
            f"/reminders/{REMINDER_A_ID}",
            json={"status": internal_status},
        )
        assert response.status_code == 422


def test_update_non_pending_reminder_returns_current_404_behavior(
    client,
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"], "sent")],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.put(
        f"/reminders/{REMINDER_A_ID}",
        json={"channel": "email"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Recordatorio no encontrado"


def test_delete_reminder_returns_204_and_then_404(
    client,
    fake_supabase_client,
    user_a,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_A_ID, TASK_A_ID, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    delete_response = client.delete(f"/reminders/{REMINDER_A_ID}")
    get_response = client.get(f"/reminders/{REMINDER_A_ID}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


def test_delete_reminder_rejects_other_user(
    client,
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_B_ID, TASK_B_ID, user_b["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.delete(f"/reminders/{REMINDER_B_ID}")

    assert response.status_code == 404


def test_reminder_validation_rejects_invalid_payloads(client, user_a):
    app.dependency_overrides[get_current_user] = lambda: user_a

    invalid_payloads = [
        {"task_id": TASK_A_ID, "remind_at": "2026-10-01T20:00:00Z", "channel": "sms"},
        {"task_id": TASK_A_ID, "remind_at": "not-a-date", "channel": "in_app"},
        {"remind_at": "2026-10-01T20:00:00Z", "channel": "in_app"},
        {**reminder_payload(), "extra": True},
        {**reminder_payload(), "status": "sent"},
    ]

    for payload in invalid_payloads:
        response = client.post("/reminders", json=payload)
        assert response.status_code == 422


def test_protected_reminders_request_without_authentication(client):
    response = client.get("/reminders")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_protected_reminders_request_with_invalid_token(
    client,
    fake_supabase_client,
    monkeypatch,
):
    fake_supabase_client.auth.get_user = Mock(side_effect=Exception("invalid"))
    monkeypatch.setattr(
        "apps.backend.app.core.security.create_authenticated_client",
        Mock(return_value=fake_supabase_client),
    )

    response = client.get(
        "/reminders",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido o expirado"


def test_user_a_cannot_operate_on_user_b_reminder(
    client,
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "reminders",
        [reminder_row(REMINDER_B_ID, TASK_B_ID, user_b["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    list_response = client.get("/reminders")
    get_response = client.get(f"/reminders/{REMINDER_B_ID}")
    update_response = client.put(
        f"/reminders/{REMINDER_B_ID}",
        json={"channel": "email"},
    )
    delete_response = client.delete(f"/reminders/{REMINDER_B_ID}")

    assert list_response.json() == []
    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
