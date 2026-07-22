from fastapi import APIRouter

from apps.backend.app.db.supabase import supabase

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

