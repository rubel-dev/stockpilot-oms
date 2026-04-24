from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StockPilot OMS API"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = "postgresql://postgres:postgres@localhost:5432/stockpilot_oms"
    database_min_pool_size: int = 1
    database_max_pool_size: int = 10

    jwt_secret_key: str = "change-me-in-production-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
