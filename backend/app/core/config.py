from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    database_url: PostgresDsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_bos"
    secret_key: str = "replace-with-secure-env-value"
    access_token_expire_minutes: int = 60
    redis_url: str = "redis://localhost:6379/0"

settings = Settings()
