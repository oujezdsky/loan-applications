from typing import Optional
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_DB_URL: PostgresDsn
    TEST_POSTGRES_DB_URL: Optional[PostgresDsn] = None
    SYNC_POSTGRES_DB_URL: PostgresDsn
    SYNC_TEST_POSTGRES_DB_URL: Optional[PostgresDsn] = None
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Redis specific settings
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_HEALTH_CHECK_INTERVAL: int = 30

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
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

    @field_validator("POSTGRES_DB_URL", mode="before")
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

    @property
    def is_testing(self):
        return self.ENVIRONMENT == "testing"

    @property
    def redis_connection_kwargs(self):
        return {
            "max_connections": self.REDIS_MAX_CONNECTIONS,
            "socket_timeout": self.REDIS_SOCKET_TIMEOUT,
            "socket_connect_timeout": self.REDIS_SOCKET_CONNECT_TIMEOUT,
            "retry_on_timeout": self.REDIS_RETRY_ON_TIMEOUT,
            "health_check_interval": self.REDIS_HEALTH_CHECK_INTERVAL,
            "decode_responses": True,
        }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
