from fastapi import APIRouter, Depends
from apps.backend.app.core.security import get_current_user

from apps.backend.app.schemas.auth import RegisterUser, LoginUser
from apps.backend.app.services.auth_service import (
    register_user,
    login_user,
)
from apps.backend.app.core.security import verify_token

router = APIRouter()


@router.post("/register", tags=["Auth"])
def register(user: RegisterUser):
    return register_user(user)


@router.post("/login", tags=["Auth"])
def login(user: LoginUser):
    return login_user(user)


@router.get("/verify-token", tags=["Auth"])
def verify(current_user=Depends(get_current_user)):

    return {
        "success": True,
        "payload": current_user
    }