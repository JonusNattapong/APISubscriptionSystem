import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "AI Model API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://yourdomain.com",
    ]
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-jwt-must-be-very-secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./ai_subscription.db"
    )
    
    # Stripe settings
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Google Cloud Storage settings
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
    GCS_CREDENTIALS_FILE: str = os.getenv("GCS_CREDENTIALS_FILE", "")
    
    # AI model settings
    MODEL_DIR: str = os.getenv("MODEL_DIR", "./models")

    # Rate limiting settings
    RATE_LIMIT_DEFAULT: int = 100  # requests per minute
    RATE_LIMIT_FREE_TIER: int = 10  # requests per minute
    RATE_LIMIT_STARTER: int = 50  # requests per minute
    RATE_LIMIT_PRO: int = 200  # requests per minute
    RATE_LIMIT_ENTERPRISE: int = 1000  # requests per minute

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
