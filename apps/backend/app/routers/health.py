from fastapi import APIRouter

from apps.backend.app.db.supabase import supabase
from apps.backend.app.schemas.profile import ProfileCreate

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "IKAROS",
        "version": "1.0.0"
    }


@router.get("/health/database", tags=["Health"])
def database_health():
    try:
        supabase.table("_health_check").select("*").limit(1).execute()

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(e)
        }

@router.post("/profiles", tags=["Profiles"])
def create_profile(profile: ProfileCreate):

    data = {
        "email": profile.email,
        "full_name": profile.full_name,
        "avatar_url": profile.avatar_url,
    }

    response = (
        supabase
        .table("profiles")
        .insert(data)
        .execute()
    )

    return response.data