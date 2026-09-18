import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    DEV_MODE: bool = True
    LOG_LEVEL: str = "INFO"

    # Gateway / Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DASHBOARD_PORT: int = 3000

    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/ai_calling.db"
    REDIS_URL: str = ""

    # PBX / Asterisk
    PBX_HOST: str = "127.0.0.1"
    PBX_PORT: int = 8088
    PBX_ARI_USERNAME: str = "ai-agent"
    PBX_ARI_PASSWORD: str = "changeme_ari_secret"
    PBX_ARI_APP: str = "ai-agent"

    SIP_EXTENSION: str = "7000"
    SIP_USERNAME: str = "ai-agent"
    SIP_PASSWORD: str = "changeme_sip_secret"
    SIP_DOMAIN: str = "127.0.0.1"

    # AI Providers
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"

    STT_PROVIDER: str = "mock"
    STT_API_KEY: str = ""
    STT_MODEL: str = "whisper-1"

    TTS_PROVIDER: str = "mock"
    TTS_API_KEY: str = ""
    TTS_MODEL: str = "tts-1"
    TTS_VOICE: str = "alloy"

    # Security
    RECORD_CALLS: bool = False
    JWT_SECRET: str = "super_secret_jwt_key_bilingual_ai_calling_2026"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

# Ensure local data directory exists if using SQLite
if "sqlite" in settings.DATABASE_URL:
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
