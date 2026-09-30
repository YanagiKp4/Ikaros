from unittest.mock import Mock

from apps.backend.app.core.security import get_current_user
from apps.backend.app.main import app


TASK_B_ID = "00000000-0000-0000-0000-000000000022"


def task_payload():
    return {
        "title": "Router task",
        "description": "Task router test",
        "status": "pending",
        "priority": "medium",
        "due_date": "2026-10-02T20:00:00Z",
    }


def task_row(task_id, user_id, title="Seeded task"):
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


def test_create_task_returns_201_and_authenticated_owner(
    client,
    fake_supabase_client,
    user_a,
):
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post("/tasks", json=task_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == user_a["id"]
    assert body["title"] == "Router task"
    assert body["status"] == "pending"
    assert fake_supabase_client.operations[-1]["payload"]["user_id"] == user_a[
        "id"
    ]


def test_list_tasks_returns_only_authenticated_users_tasks(
    client,
    fake_supabase_client,
    user_a,
    user_b,
):
    fake_supabase_client.seed(
        "tasks",
        [
            task_row("00000000-0000-0000-0000-000000000011", user_a["id"]),
            task_row(TASK_B_ID, user_b["id"], "User B task"),
        ],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["user_id"] == user_a["id"]


def test_get_task_returns_200_for_owned_task(
    client,
    fake_supabase_client,
    user_a,
):
    task_id = "00000000-0000-0000-0000-000000000011"
    fake_supabase_client.seed(
        "tasks",
        [task_row(task_id, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_missing_task_returns_404(client, user_a):
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.get("/tasks/00000000-0000-0000-0000-000000000099")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_task_returns_200_for_owned_task(
    client,
    fake_supabase_client,
    user_a,
):
    task_id = "00000000-0000-0000-0000-000000000011"
    fake_supabase_client.seed(
        "tasks",
        [task_row(task_id, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated router task"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated router task"


def test_update_task_rejects_user_id_in_body(client, user_a):
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.put(
        "/tasks/00000000-0000-0000-0000-000000000011",
        json={"user_id": user_a["id"]},
    )

    assert response.status_code == 422


def test_delete_task_returns_204_for_owned_task(
    client,
    fake_supabase_client,
    user_a,
):
    task_id = "00000000-0000-0000-0000-000000000011"
    fake_supabase_client.seed(
        "tasks",
        [task_row(task_id, user_a["id"])],
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204
    assert response.content == b""


def test_protected_tasks_request_without_authentication(client):
    response = client.get("/tasks")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_protected_tasks_request_with_invalid_token(
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
        "/tasks",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido o expirado"


def test_user_cannot_get_update_or_delete_another_users_task(
    client,
    fake_supabase_client,
    user_a,
    user_b,
):
    app.dependency_overrides[get_current_user] = lambda: user_b
    create_response = client.post("/tasks", json=task_payload())
    task_id = create_response.json()["id"]

    app.dependency_overrides[get_current_user] = lambda: user_a
    get_response = client.get(f"/tasks/{task_id}")
    update_response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Unauthorized update"},
    )
    delete_response = client.delete(f"/tasks/{task_id}")

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    assert fake_supabase_client.tables["tasks"][0]["user_id"] == user_b[
        "id"
    ]


def test_task_validation_rejects_invalid_body(client, user_a):
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post(
        "/tasks",
        json={"title": "x"},
    )

    assert response.status_code == 422


def test_task_validation_rejects_missing_required_title(client, user_a):
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post(
        "/tasks",
        json={"description": "Missing title"},
    )

    assert response.status_code == 422


def test_task_validation_rejects_extra_field(client, user_a):
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.post(
        "/tasks",
        json={**task_payload(), "user_id": user_a["id"]},
    )

    assert response.status_code == 422
