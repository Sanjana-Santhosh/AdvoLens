from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router as api_router
from app.api.issues import router as issues_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.notifications import router as notifications_router
from app.api.analytics import router as analytics_router
from app.api.engagement import router as engagement_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle for the app."""
    # Startup: warm up ML models
    print("Warming up ML models...")
    from app.ml.clip_service import clip_service  # noqa: F401
    from app.ml.faiss_manager import faiss_manager  # noqa: F401
    print("ML models ready.")
    yield
    # Shutdown: persist Faiss index
    faiss_manager.save_index()
    print("Faiss index saved.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AdvoLens API",
        version="0.1.0",
        description="Backend API for AdvoLens civic issue reporting platform",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Local dev
            "http://127.0.0.1:3000",
            "http://192.168.1.37:3000",
            "https://advolens.vercel.app",  # Production (update after deployment)
            "https://*.vercel.app",  # All Vercel preview URLs
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include main API router
    app.include_router(api_router, prefix="/api")
    app.include_router(issues_router, prefix="/issues")
    app.include_router(auth_router, prefix="/auth")
    app.include_router(admin_router, prefix="/admin")
    app.include_router(notifications_router, prefix="/notifications")
    app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
    app.include_router(engagement_router, prefix="/issues", tags=["engagement"])

    # Health check endpoint for Docker/Kubernetes
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "advolens-backend"}

    # Serve uploaded images
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    return app

app = create_app()
