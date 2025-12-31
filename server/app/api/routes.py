from fastapi import APIRouter
from app.api.config import router as config_router

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "AdvoLens API"}

# Mount sub-routers
router.include_router(config_router)
