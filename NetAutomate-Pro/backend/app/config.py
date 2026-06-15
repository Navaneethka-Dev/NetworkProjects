"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "NetAutomate Pro"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_openssl_rand_hex_32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://netautomate:netautomate@localhost:5432/netautomate"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Network / Devices ─────────────────────────────────────────────────────
    MOCK_DEVICES: bool = True            # False → real SSH via Netmiko
    DEVICE_SSH_TIMEOUT: int = 30
    DEVICE_PASSWORD_ENCRYPTION_KEY: str = "CHANGE_ME_32_BYTE_KEY_BASE64=="

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── Backup storage ────────────────────────────────────────────────────────
    BACKUP_RETENTION_DAYS: int = 90
    BACKUP_MAX_PER_DEVICE: int = 50

    # ── Scheduled tasks ───────────────────────────────────────────────────────
    SCHEDULED_BACKUP_INTERVAL_HOURS: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
