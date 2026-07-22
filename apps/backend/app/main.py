from fastapi import FastAPI

from apps.backend.app.routers.health import router as health_router
from apps.backend.app.routers.profiles import router as profiles_router

app = FastAPI(
    title="IKAROS API",
    version="1.0.0",
    description="Backend principal de IKAROS"
)

app.include_router(health_router)
app.include_router(profiles_router)


@app.get("/")
def root():
    return {
        "message": "Bienvenido a IKAROS 🚀"
    }