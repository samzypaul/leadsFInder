"""Central configuration loaded from environment variables / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — defaults to local SQLite so the app runs with zero setup.
    database_url: str = "sqlite:///./leadhunter.db"

    # AI
    ai_provider: str = "gemini"  # gemini | openai | fallback
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Search
    google_search_api_key: str | None = None
    google_search_cx: str | None = None

    # Scraping
    scraper_mode: str = "fallback"  # live | fallback
    respect_robots: bool = True
    scraper_user_agent: str = "LeadHunterTZ/1.0 (+https://example.com/bot)"
    scraper_timeout_seconds: int = 20
    scraper_min_delay: float = 2.0

    # App
    cors_origins: str = "http://localhost:3000"
    default_country: str = "Tanzania"

    # Auth / security
    auth_enabled: bool = True
    secret_key: str = "change-me-in-production-please-set-SECRET_KEY"
    access_token_expire_minutes: int = 60 * 12  # 12h
    admin_email: str = "admin@leadhunter.tz"
    admin_password: str = "changeme"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        if self.ai_provider == "gemini":
            return bool(self.gemini_api_key)
        if self.ai_provider == "openai":
            return bool(self.openai_api_key)
        return False

    @property
    def search_enabled(self) -> bool:
        return bool(self.google_search_api_key and self.google_search_cx)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
