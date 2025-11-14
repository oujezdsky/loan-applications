import pytest
from fastapi.testclient import TestClient
from app.utils.logging import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError
from respx import MockRouter
import httpx
from app.utils.caching import get_redis_client


@pytest.mark.asyncio
async def test_health_endpoint(test_client: TestClient):
    """Test the /health endpoint returns correct status when all dependencies are healthy."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dependencies": {"redis": "ok", "api": "ok"},
    }
    logger.debug("Health endpoint test passed")


@pytest.mark.asyncio
async def test_health_endpoint_redis_failure(
    test_client: TestClient, mock_redis: Redis
):
    """Test the /health endpoint when Redis is unavailable."""

    async def mock_get_redis_client():
        mock_redis.ping.side_effect = RedisError("Redis connection failed")  # type: ignore
        yield mock_redis

    test_client.app.dependency_overrides[get_redis_client] = mock_get_redis_client  # type: ignore

    response = test_client.get("/health")
    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "dependencies": {"redis": "error: Redis connection failed", "api": "ok"},
    }
    assert response.headers["X-Error-Code"] == "456"
    logger.debug("Health endpoint Redis failure test passed")

    test_client.app.dependency_overrides.clear()  # type: ignore


@pytest.mark.asyncio
async def test_health_endpoint_api_failure(
    test_client: TestClient, mock_http_client: MockRouter, mock_redis: Redis
):
    """Test the /health endpoint when 3rd party API is unavailable."""

    async def mock_get_redis_client():
        yield mock_redis

    test_client.app.dependency_overrides[get_redis_client] = mock_get_redis_client  # type: ignore

    mock_http_client.get("https://api.freecurrencyapi.com/v1/status").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )

    response = test_client.get("/health")
    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "dependencies": {
            "redis": "ok",
            "api": "error: Request failed with status code 500",
        },
    }
    assert response.headers["X-Error-Code"] == "456"
    logger.debug("Health endpoint API failure test passed")

    test_client.app.dependency_overrides.clear()  # type: ignore
