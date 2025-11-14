import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from unittest.mock import AsyncMock
import httpx
from respx import MockRouter
from typing import AsyncGenerator, Dict
from app.main import app
from app.config import Settings
from app.utils.logging import logger


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test-specific settings matching the production configuration."""
    settings = Settings(
        ENVIRONMENT="testing",
        LOG_LEVEL="DEBUG",
        THIRD_PARTY_API_LATEST_URL="https://api.freecurrencyapi.com/v1/latest",
        THIRD_PARTY_API_STATUS_URL="https://api.freecurrencyapi.com/v1/status",
        THIRD_PARTY_API_KEY="test_key",
        THIRD_PARTY_API_BASE_CURRENCY="EUR",
        REDIS_URL="redis://redis:6379/0",
        REFRESH_INTERVAL_HOURS=2,
        HEARTBEAT_INTERVAL_SECONDS=2,
        PONG_TIMEOUT_SECONDS=1,
        PORT=8000,
        THE_ERROR_STATUS_CODE=456,
    )
    logger.debug(f"Test settings initialized: {settings.model_dump()}")
    return settings


@pytest_asyncio.fixture(scope="session")
async def test_client(test_settings: Settings) -> AsyncGenerator[TestClient, None]:
    """Provide FastAPI test client with overridden settings."""
    app.dependency_overrides[lambda: Settings()] = lambda: test_settings  # type: ignore
    client = TestClient(app)
    logger.debug("Test client initialized")
    yield client
    app.dependency_overrides.clear()
    logger.debug("Test client cleaned up")


@pytest_asyncio.fixture(scope="function")
async def mock_redis() -> AsyncGenerator[AsyncMock, None]:
    """Mock Redis client with in-memory dictionary for testing."""
    redis_data: Dict[str, str] = {}

    async def get(key: str) -> str | None:
        return redis_data.get(key)

    async def set(key: str, value: str, ex: int | None = None) -> None:
        redis_data[key] = str(value)

    async def ping() -> bool:
        return True

    async def aclose() -> None:
        redis_data.clear()

    mock = AsyncMock(spec=Redis)
    mock.get.side_effect = get
    mock.set.side_effect = set
    mock.ping.side_effect = ping
    mock.aclose.side_effect = aclose

    logger.debug("Mock Redis initialized")
    yield mock
    await mock.aclose()
    logger.debug("Mock Redis cleaned up")


@pytest_asyncio.fixture(scope="function")
async def mock_http_client(test_settings: Settings) -> AsyncGenerator[MockRouter, None]:
    """Mock HTTP client for 3rd party API calls."""
    with MockRouter(assert_all_called=False) as respx_mock:
        respx_mock.get("https://api.freecurrencyapi.com/v1/status").mock(
            return_value=httpx.Response(
                200,
                json={
                    "quotas": {"month": {"total": 300, "used": 71, "remaining": 229}}
                },
            )
        )
        respx_mock.get("https://api.freecurrencyapi.com/v1/latest").mock(
            return_value=httpx.Response(
                200,
                json={"data": {"USD": 1.23, "CZK": 22.5}},
                headers={"content-type": "application/json"},
            )
        )
        logger.debug("Mock HTTP client initialized")
        yield respx_mock
        logger.debug("Mock HTTP client cleaned up")
