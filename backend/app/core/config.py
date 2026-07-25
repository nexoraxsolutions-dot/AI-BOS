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
    refresh_token_expire_minutes: int = 10080  # 7 days
    redis_url: str = "redis://localhost:6379/0"

    # Email configuration
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from_address: str = "noreply@ai-bos.com"
    email_from_name: str = "AI-BOS"
    email_verification_token_expire_hours: int = 48
    frontend_url: str = "http://localhost:3000"

settings = Settings()
