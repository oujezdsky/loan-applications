from contextlib import asynccontextmanager
from typing import AsyncIterator
import httpx
from httpx._transports.default import AsyncHTTPTransport
from app.logging_config import logger


@asynccontextmanager
async def http_client(
    timeout: float = 10.0, retries: int = 3
) -> AsyncIterator[httpx.AsyncClient]:
    """Provide an async HTTP client with timeout and retry configuration."""
    transport = AsyncHTTPTransport(retries=retries)
    client = httpx.AsyncClient(
        timeout=httpx.Timeout(timeout),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        follow_redirects=True,
        transport=transport,
    )
    try:
        logger.debug(
            "HTTP client initialized with timeout=%s, retries=%s", timeout, retries
        )
        yield client
    except Exception as e:
        logger.error("HTTP client error: %s", str(e))
        raise
    finally:
        await client.aclose()
        logger.debug("HTTP client closed")
