from fastapi import FastAPI
from app.api.routes import router as api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="AdvoLens API",
        version="0.1.0",
        description="Backend API for AdvoLens civic issue reporting platform",
    )

    # Include main API router
    app.include_router(api_router, prefix="/api")

    return app

app = create_app()
