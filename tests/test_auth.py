from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from postgrest import APIError
from supabase_auth.errors import AuthApiError

from apps.backend.app.schemas.auth import LoginUser, RegisterUser
from apps.backend.app.services import auth_service
from apps.backend.app.core import security


TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test-password"
TEST_TOKEN = "test-access-token"


def auth_user():
    return SimpleNamespace(
        id=TEST_USER_ID,
        email=TEST_EMAIL,
        user_metadata={"full_name": "Auth User"},
    )


def auth_session():
    return SimpleNamespace(
        access_token=TEST_TOKEN,
        refresh_token="test-refresh-token",
        token_type="bearer",
        expires_in=3600,
        expires_at=1_900_000_000,
    )


def test_register_user_uses_provided_public_client(fake_supabase_client, monkeypatch):
    response = SimpleNamespace(
        user=auth_user(),
        session=auth_session(),
    )
    fake_supabase_client.auth.sign_up = Mock(return_value=response)
    create_client = Mock(return_value=fake_supabase_client)
    monkeypatch.setattr(auth_service, "create_public_client", create_client)

    result = auth_service.register_user(
        RegisterUser(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            full_name="Auth User",
        )
    )

    create_client.assert_called_once_with()
    fake_supabase_client.auth.sign_up.assert_called_once_with({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "options": {
            "data": {
                "full_name": "Auth User",
            }
        },
    })
    assert result["success"] is True
    assert result["user"] == {
        "id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "full_name": "Auth User",
    }
    assert result["access_token"] == TEST_TOKEN
    assert result["email_confirmation_required"] is False


def test_register_user_maps_auth_error(fake_supabase_client, monkeypatch):
    fake_supabase_client.auth.sign_up = Mock(
        side_effect=AuthApiError(
            "Registration failed",
            "400",
            "registration_failed",
        )
    )
    monkeypatch.setattr(
        auth_service,
        "create_public_client",
        Mock(return_value=fake_supabase_client),
    )

    with pytest.raises(HTTPException) as error:
        auth_service.register_user(
            RegisterUser(
                email=TEST_EMAIL,
                password=TEST_PASSWORD,
                full_name="Auth User",
            )
        )

    assert error.value.status_code == 400
    assert error.value.detail == "No se pudo registrar el usuario"


def test_login_user_uses_credentials_and_returns_session(
    fake_supabase_client,
    monkeypatch,
):
    response = SimpleNamespace(
        user=auth_user(),
        session=auth_session(),
    )
    fake_supabase_client.auth.sign_in_with_password = Mock(
        return_value=response
    )
    create_client = Mock(return_value=fake_supabase_client)
    monkeypatch.setattr(auth_service, "create_public_client", create_client)

    result = auth_service.login_user(
        LoginUser(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
        )
    )

    create_client.assert_called_once_with()
    fake_supabase_client.auth.sign_in_with_password.assert_called_once_with({
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert result["success"] is True
    assert result["message"] == "Login exitoso"
    assert result["user"]["id"] == TEST_USER_ID
    assert result["access_token"] == TEST_TOKEN
    assert result["refresh_token"] == "test-refresh-token"


def test_login_user_maps_invalid_credentials(fake_supabase_client, monkeypatch):
    fake_supabase_client.auth.sign_in_with_password = Mock(
        side_effect=AuthApiError(
            "Invalid credentials",
            "401",
            "invalid_credentials",
        )
    )
    monkeypatch.setattr(
        auth_service,
        "create_public_client",
        Mock(return_value=fake_supabase_client),
    )

    with pytest.raises(HTTPException) as error:
        auth_service.login_user(
            LoginUser(
                email=TEST_EMAIL,
                password=TEST_PASSWORD,
            )
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Credenciales inválidas"


def test_get_current_user_requires_credentials():
    with pytest.raises(HTTPException) as error:
        security.get_current_user(None)

    assert error.value.status_code == 401
    assert error.value.detail == "Authentication required"


def test_get_current_user_rejects_invalid_token(
    fake_supabase_client,
    monkeypatch,
):
    fake_supabase_client.auth.get_user = Mock(side_effect=Exception("invalid"))
    create_client = Mock(return_value=fake_supabase_client)
    monkeypatch.setattr(security, "create_authenticated_client", create_client)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=TEST_TOKEN,
    )

    with pytest.raises(HTTPException) as error:
        security.get_current_user(credentials)

    create_client.assert_called_once_with(TEST_TOKEN)
    assert error.value.status_code == 401
    assert error.value.detail == "Token inválido o expirado"


def test_get_current_user_returns_authenticated_context(
    fake_supabase_client,
    monkeypatch,
):
    fake_supabase_client.auth.get_user = Mock(
        return_value=SimpleNamespace(user=auth_user())
    )
    create_client = Mock(return_value=fake_supabase_client)
    monkeypatch.setattr(security, "create_authenticated_client", create_client)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=TEST_TOKEN,
    )

    result = security.get_current_user(credentials)

    create_client.assert_called_once_with(TEST_TOKEN)
    fake_supabase_client.auth.get_user.assert_called_once_with(jwt=TEST_TOKEN)
    assert result["id"] == TEST_USER_ID
    assert result["email"] == TEST_EMAIL
    assert result["full_name"] == "Auth User"
    assert result["access_token"] == TEST_TOKEN
    assert result["client"] is fake_supabase_client


def test_verify_token_returns_public_payload_without_client(
    client,
    fake_supabase_client,
    monkeypatch,
):
    fake_supabase_client.auth.get_user = Mock(
        return_value=SimpleNamespace(user=auth_user())
    )
    monkeypatch.setattr(
        security,
        "create_authenticated_client",
        Mock(return_value=fake_supabase_client),
    )

    response = client.get(
        "/verify-token",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "success": True,
        "payload": {
            "id": TEST_USER_ID,
            "email": TEST_EMAIL,
            "full_name": "Auth User",
        },
    }
    assert "client" not in body["payload"]
    assert "access_token" not in body["payload"]


def test_verify_token_requires_bearer_credentials(client):
    response = client.get("/verify-token")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_verify_token_rejects_invalid_authorization_scheme(client):
    response = client.get(
        "/verify-token",
        headers={"Authorization": "Basic invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_verify_token_rejects_invalid_token(
    client,
    fake_supabase_client,
    monkeypatch,
):
    fake_supabase_client.auth.get_user = Mock(return_value=None)
    monkeypatch.setattr(
        security,
        "create_authenticated_client",
        Mock(return_value=fake_supabase_client),
    )

    response = client.get(
        "/verify-token",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido o expirado"
