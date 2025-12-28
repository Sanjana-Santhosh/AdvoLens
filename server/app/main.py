from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router as api_router
from app.api.issues import router as issues_router


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
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.1.37:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include main API router
    app.include_router(api_router, prefix="/api")
    app.include_router(issues_router, prefix="/issues")

    # Serve uploaded images
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    return app

app = create_app()
