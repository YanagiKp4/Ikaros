from fastapi import FastAPI

from apps.backend.app.db.supabase import supabase
from apps.backend.app.routers.health import router as health_router

app = FastAPI(
    title="IKAROS API",
    version="1.0.0",
    description="Backend principal de IKAROS"
)

app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "Bienvenido a IKAROS 🚀"
    }