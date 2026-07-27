from datetime import datetime, timedelta

from jose import JWTError, jwt

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from apps.backend.app.services.user_service import get_user_by_email


SECRET_KEY = "IKAROS_SUPER_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str):

    print("=" * 50)
    print("TOKEN RECIBIDO:")
    print(token)

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        print("PAYLOAD:")
        print(payload)

        return payload

    except JWTError as e:
        print("ERROR JWT:")
        print(e)
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )

    users = get_user_by_email(payload["sub"])

    if len(users) == 0:
        raise HTTPException(
            status_code=401,
            detail="Usuario no encontrado"
        )

    db_user = users[0]

    return {
        "id": db_user["id"],
        "email": db_user["email"],
        "full_name": db_user["full_name"]
    }