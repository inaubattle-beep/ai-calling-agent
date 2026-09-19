from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from sqlalchemy.orm import declarative_base

from .config import settings

# Engine configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    # SQLite compatibility for multithreaded/async execution
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if "sqlite" in settings.DATABASE_URL:
            columns = {
                "description": "TEXT NOT NULL DEFAULT 'AI voice agent'",
                "greeting": "TEXT NOT NULL DEFAULT 'Hello, how can I help you?'",
                "system_prompt": "TEXT NOT NULL DEFAULT 'You are a polite, helpful telephone AI receptionist.'",
                "supported_languages": "TEXT NOT NULL DEFAULT '[\"bn-BD\", \"en-US\", \"mixed\"]'",
                "enabled": "BOOLEAN NOT NULL DEFAULT 1",
            }
            result = await conn.execute(text("PRAGMA table_info(agents)"))
            existing = {row[1] for row in result.fetchall()}
            for name, definition in columns.items():
                if name not in existing:
                    await conn.execute(text(f"ALTER TABLE agents ADD COLUMN {name} {definition}"))
