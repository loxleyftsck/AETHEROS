"""
Application settings — loaded from environment / .env file.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Security ─────────────────────────────────────────────────────────────
    API_SECRET_KEY: str = "goldmine-dev-secret"
    API_KEY_HEADER: str = "X-API-Key"

    # ── LLM ──────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_PROVIDER: str = "openai"  # "openai" | "ollama"

    # ── Market Data ──────────────────────────────────────────────────────────
    ALPHA_VANTAGE_API_KEY: str = ""          # Optional premium market data
    SERPER_API_KEY: str = ""                 # Web search
    FEAR_GREED_UPDATE_INTERVAL: int = 3600   # seconds

    # ── Social Sentiment ─────────────────────────────────────────────────────
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "AgentOS-Goldmine/1.0"
    TWITTER_BEARER_TOKEN: str = ""           # Optional

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./goldmine.db"

    # ── Memory ───────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    SHORT_TERM_TOKEN_LIMIT: int = 4096

    # ── Reports ───────────────────────────────────────────────────────────────
    REPORTS_DIR: str = "./reports"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
