from datetime import datetime, timezone
from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
async def get_health():
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "dev_mode": settings.DEV_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": "online",
            "telephony": "mock" if settings.DEV_MODE else "asterisk",
            "llm": settings.LLM_PROVIDER,
            "stt": settings.STT_PROVIDER,
            "tts": settings.TTS_PROVIDER,
            "redis": "configured" if settings.REDIS_URL else "in-memory-fallback",
        },
    }
