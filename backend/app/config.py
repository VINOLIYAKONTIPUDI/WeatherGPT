from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "WeatherGPT"
    app_env: Literal["development", "production", "test"] = "development"
    demo_mode: bool = True
    secret_key: str = "change-me-in-production-weathergpt-sih-26068"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./weathergpt.db"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    weather_provider: str = "open_meteo"
    weather_api_key: str = ""
    weather_api_base_url: str = "https://api.open-meteo.com/v1"
    weather_geocode_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    weather_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"

    llm_provider: str = "openai_compat"
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    demo_otp: str = "123456"
    otp_expire_minutes: int = 10

    weather_cache_ttl_seconds: int = 600
    rate_limit: str = "60/minute"

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
