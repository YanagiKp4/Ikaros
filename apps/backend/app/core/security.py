from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.backend.app.db.supabase import create_authenticated_client


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = credentials.credentials
    client = create_authenticated_client(access_token)

    try:
        response = client.auth.get_user(jwt=access_token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if response is None or response.user is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    auth_user = response.user
    metadata = auth_user.user_metadata or {}

    return {
        "id": auth_user.id,
        "email": auth_user.email,
        "full_name": metadata.get("full_name"),
        "access_token": access_token,
        "client": client,
    }
