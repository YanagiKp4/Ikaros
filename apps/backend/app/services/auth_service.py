import bcrypt

from apps.backend.app.db.supabase import supabase
from apps.backend.app.schemas.auth import RegisterUser, LoginUser
from apps.backend.app.core.security import create_access_token
from apps.backend.app.services.user_service import get_user_by_email

def register_user(user: RegisterUser):

    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    data = {
        "email": user.email,
        "password": hashed_password,
        "full_name": user.full_name,
    }

    response = (
        supabase
        .table("users")
        .insert(data)
        .execute()
    )

    return response.data


def login_user(user: LoginUser):

    users = get_user_by_email(user.email)

    if len(users) == 0:
        return {
            "success": False,
            "message": "Usuario no encontrado"
        }

    db_user = users[0]

    password_correct = bcrypt.checkpw(
        user.password.encode("utf-8"),
        db_user["password"].encode("utf-8")
    )

    if not password_correct:
        return {
            "success": False,
            "message": "Contraseña incorrecta"
        }

    access_token = create_access_token(
        {
            "sub": db_user["email"]
        }
    )

    return {
        "success": True,
        "message": "Login exitoso",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "email": db_user["email"],
            "full_name": db_user["full_name"]
        }
    }