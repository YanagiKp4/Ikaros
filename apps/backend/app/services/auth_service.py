from fastapi import HTTPException, status
from supabase_auth.errors import AuthApiError

from apps.backend.app.db.supabase import create_public_client
from apps.backend.app.schemas.auth import RegisterUser, LoginUser


def _serialize_user(user):
    if user is None:
        return None

    metadata = user.user_metadata or {}

    return {
        "id": user.id,
        "email": user.email,
        "full_name": metadata.get("full_name"),
    }


def _session_data(session):
    if session is None:
        return {
            "email_confirmation_required": True
        }

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "token_type": session.token_type,
        "expires_in": session.expires_in,
        "expires_at": session.expires_at,
        "email_confirmation_required": False,
    }


def register_user(user: RegisterUser):
    client = create_public_client()

    try:
        response = client.auth.sign_up({
            "email": str(user.email),
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name
                }
            }
        })
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo registrar el usuario"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de autenticación no está disponible"
        ) from exc

    if response.user is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase no devolvió el usuario registrado"
        )

    result = {
        "success": True,
        "message": "Registro exitoso",
        "user": _serialize_user(response.user),
    }
    result.update(_session_data(response.session))
    return result


def login_user(user: LoginUser):
    client = create_public_client()

    try:
        response = client.auth.sign_in_with_password({
            "email": str(user.email),
            "password": user.password,
        })
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de autenticación no está disponible"
        ) from exc

    if response.user is None or response.session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo crear una sesión"
        )

    result = {
        "success": True,
        "message": "Login exitoso",
        "user": _serialize_user(response.user),
    }
    result.update(_session_data(response.session))
    return result
