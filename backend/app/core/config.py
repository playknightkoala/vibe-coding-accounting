from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cloudflare Turnstile
    TURNSTILE_SECRET_KEY: str = "CHANGE_THIS_TURNSTILE_SECRET_KEY_MIN_32_CHARS"

    # Data Encryption Key (用於加密匯出的資料)
    DATA_ENCRYPTION_KEY: str = "CHANGE_THIS_DATA_ENCRYPTION_KEY_MIN_32_CHARS"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Environment
    ENVIRONMENT: str = "production"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True

    # Email (SMTP) Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Accounting System"

    # Frontend URL (for password reset links)
    FRONTEND_URL: str = "http://localhost"
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

    @property
    def cors_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]

    def validate_security(self):
        """Validate security settings"""
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if self.ENVIRONMENT == "production":
            if "localhost" in self.ALLOWED_ORIGINS:
                raise ValueError("localhost should not be in ALLOWED_ORIGINS in production")
            if self.SECRET_KEY in ["your-secret-key-change-this-in-production-please",
                                    "CHANGE_THIS_TO_RANDOM_SECRET_KEY_MIN_32_CHARS"]:
                raise ValueError("You must change SECRET_KEY from the default value in production")

# Update DATABASE_URL to use psycopg driver
settings = Settings()
if settings.DATABASE_URL.startswith("postgresql://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Validate security settings in production
if settings.ENVIRONMENT == "production":
    settings.validate_security()
