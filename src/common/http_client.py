"""Shared HTTP client with connection pooling."""
import httpx
from typing import Optional
from .config import get_settings


# Singleton HTTP client instance
_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """
    Get or create shared HTTP client with connection pooling.

    This prevents creating a new client for every request,
    significantly improving performance.
    """
    global _http_client

    if _http_client is None:
        settings = get_settings()
        _http_client = httpx.AsyncClient(
            timeout=settings.vacancy_timeout,
            limits=httpx.Limits(
                max_keepalive_connections=settings.http_keepalive_connections,
                max_connections=settings.http_max_connections,
            ),
        )

    return _http_client


async def close_http_client() -> None:
    """Close the HTTP client."""
    global _http_client

    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
