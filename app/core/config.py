from functools import lru_cache
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Inject Streamlit Cloud secrets into environment ───────────────────────────
try:
    import streamlit as _st
    for _k, _v in _st.secrets.items():
        if isinstance(_v, str) and _k not in os.environ:
            os.environ[_k] = _v
except Exception:
    pass


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
