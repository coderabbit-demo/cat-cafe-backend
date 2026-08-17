from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cat Cafe API"
    database_url: str = "postgresql+asyncpg://catcafe:catcafe@localhost:5432/catcafe"
    jwt_secret: str = "change-me"
    service_api_token: str = "development-service-token"
    frontend_url: str = "http://localhost:8443"
    google_client_id: str = ""
    session_cookie_name: str = "cat_cafe_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 7
    session_cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
