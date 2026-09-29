from fastapi import APIRouter, HTTPException, status

from apps.backend.app.db.supabase import create_public_client

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
        create_public_client().table("users").select("id").limit(1).execute()

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database health check failed"
        ) from exc
