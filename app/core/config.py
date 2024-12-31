import os

from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field


class Settings(BaseSettings):
    # Base Settings
    PROJECT_NAME: str = "Auth Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL"))
    DATABASE_PASSWORD: str = Field(default=os.getenv("DATABASE_PASSWORD"))
    # Google OAuth2
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/api/v1/auth/google/callback")

    # CORS
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"  # This allows extra fields from .env file


settings = Settings()