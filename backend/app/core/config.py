"""Application configuration module."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Smart RoadFix API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # MongoDB
    MONGO_URI: str = Field(default="mongodb://localhost:27017")
    MONGO_DB_NAME: str = "smart_roadfix"

    # Auth0
    AUTH0_DOMAIN: str = Field(default="")
    AUTH0_AUDIENCE: str = Field(default="")
    AUTH0_ALGORITHMS: List[str] = ["RS256"]

    # Open311
    OPEN311_BASE_URL: str = Field(default="https://api.open311.org")
    OPEN311_API_KEY: Optional[str] = None
    OPEN311_SERVICE_CODE: str = "POTHOLE"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
