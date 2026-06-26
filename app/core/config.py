from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AI Community Health & Volunteer Operations Platform"
    APP_ENV: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql+asyncpg://healthuser:healthpass@localhost:5432/healthdb"
    DATABASE_URL_SYNC: str = "postgresql://healthuser:healthpass@localhost:5432/healthdb"

    JWT_SECRET_KEY: str = "change-me-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_MAPS_API_KEY: str = ""

    SUPERADMIN_EMAIL: str = "admin"
    SUPERADMIN_PASSWORD: str = "ChangeMe123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
