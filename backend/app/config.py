"""Application configuration with zero-dependency fallback."""
import os
from typing import List
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    # Load .env from project root if present
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_default_sqlite_path = os.path.join(BASE_DIR, "warehouse.db").replace("\\", "/")


class Settings(BaseModel):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_default_sqlite_path}")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "9f8c5b2a1e7d4c6b8a0e2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e4b6a8c0e2d4"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # File uploads
    UPLOADS_DIR: str = os.getenv("UPLOADS_DIR", os.path.join(BASE_DIR, "uploads"))

    # First admin seed
    FIRST_ADMIN_USERNAME: str = os.getenv("FIRST_ADMIN_USERNAME", "admin")
    FIRST_ADMIN_EMAIL: str = os.getenv("FIRST_ADMIN_EMAIL", "admin@warehouse.local")
    FIRST_ADMIN_PASSWORD: str = os.getenv("FIRST_ADMIN_PASSWORD", "admin123")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
