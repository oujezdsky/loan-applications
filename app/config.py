import os
from typing import Optional
from pydantic import BaseSettings, PostgresDsn, validator


class Settings(BaseSettings):
    # Database
    POSTGRES_DB_URL: PostgresDsn
    TEST_POSTGRES_DB_URL: Optional[PostgresDsn] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    
    # External Services
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Application Settings
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    MAX_FILE_SIZE_MB: int = 5
    VERIFICATION_TIMEOUT_HOURS: int = 24
    
    @validator("POSTGRES_DB_URL", pre=True)
    def validate_POSTGRES_DB_URL(cls, v):
        if not v:
            raise ValueError("POSTGRES_DB_URL must be set")
        return v
    
    @property
    def is_development(self):
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self):
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()