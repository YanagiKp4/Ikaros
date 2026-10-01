from apps.backend.app.routers import health


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "IKAROS",
        "version": "1.0.0",
    }


def test_database_health_is_liveness_only(client, monkeypatch):
    def fail_if_database_is_accessed(*args, **kwargs):
        raise AssertionError("database health must not access public.users")

    monkeypatch.setattr(
        health,
        "create_public_client",
        fail_if_database_is_accessed,
        raising=False,
    )

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "not_checked",
    }
