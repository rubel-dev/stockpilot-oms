from functools import lru_cache
from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_csv_origins(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


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
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
    cors_allow_origin_regex: str | None = r"^https://.*\.vercel\.app$"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @cached_property
    def cors_origins_list(self) -> list[str]:
        return parse_csv_origins(self.cors_allow_origins)


@lru_cache
def get_settings() -> Settings:
    return Settings()
