from fastapi import APIRouter
from app.core.config import settings


router = APIRouter(prefix="/config", tags=["config"])


@router.get("/model")
def get_model_config():
    return {
        "llm_model": settings.LLM_MODEL,
        "llm_enable_preview": settings.LLM_ENABLE_PREVIEW,
        "llm_provider": settings.LLM_PROVIDER,
    }
