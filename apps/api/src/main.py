from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .events.bus import event_bus
from .routers.agents import router as agents_router
from .routers.calls import router as calls_router
from .routers.events import router as events_router
from .routers.health import router as health_router
from .routers.ws import router as ws_router
from .services.call_manager import call_manager

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Calling Platform API Gateway...")
    await init_db()
    await event_bus.start()
    await call_manager.init_agent_record()
    logger.info("Database and Event Bus successfully initialized.")
    yield
    logger.info("Shutting down API Gateway...")
    await event_bus.stop()


app = FastAPI(
    title="Bilingual AI Calling Agent API",
    description="Backend API and Real-Time Gateway for Bilingual Phone Calling Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(calls_router)
app.include_router(agents_router)
app.include_router(events_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "name": "Bilingual AI Calling Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.src.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
