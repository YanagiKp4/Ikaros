from fastapi import APIRouter

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
    return {
        "status": "ok",
        "database": "not_checked"
    }
