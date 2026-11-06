import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CampusSync AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Environment & Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./campussync.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "campussync_super_secret_jwt_key_2026_ddugu_hackathon")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # AI Engine
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Host & Ports
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "3000"))

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
