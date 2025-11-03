"""
Remote implementation of VacancyClient.
Makes HTTP calls to external vacancy service.
Used in microservices mode.
"""
import httpx
from common.models import ReserveRequest, ReserveResponse, AvailableResponse
from domain.interfaces import VacancyClient
from domain.exceptions import VacancyServiceError
from common.config import get_settings
from common.http_client import get_http_client


class RemoteVacancyClient:
    """
    Remote vacancy client - HTTP calls.
    Used when vacancy service is deployed separately.

    This implementation uses HTTP with connection pooling for
    communication with the remote vacancy service.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None):
        """
        Initialize remote client.

        Args:
            http_client: Optional HTTP client. If None, will get shared client.
        """
        self.settings = get_settings()
        self.base_url = self.settings.vacancy_url
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client (lazy initialization)."""
        if self._client is None:
            self._client = await get_http_client()
        return self._client

    async def reserve(self, request: ReserveRequest) -> ReserveResponse:
        """
        Reserve tickets via HTTP.

        Args:
            request: Reservation request

        Returns:
            Reservation response

        Raises:
            VacancyServiceError: If HTTP request fails
        """
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/api/v1/reserve",
                json=request.model_dump(),
                timeout=self.settings.vacancy_timeout,
            )
            response.raise_for_status()
            return ReserveResponse(**response.json())

        except httpx.HTTPError as e:
            raise VacancyServiceError(
                f"Failed to reserve tickets: {str(e)}"
            ) from e

    async def get_available(self) -> AvailableResponse:
        """
        Get available inventory via HTTP.

        Returns:
            Available response

        Raises:
            VacancyServiceError: If HTTP request fails
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/api/v1/available",
                timeout=self.settings.vacancy_timeout,
            )
            response.raise_for_status()
            return AvailableResponse(**response.json())

        except httpx.HTTPError as e:
            raise VacancyServiceError(
                f"Failed to get availability: {str(e)}"
            ) from e

    async def health_check(self) -> bool:
        """
        Health check via HTTP.

        Returns:
            True if service is reachable and healthy, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.base_url}/api/v1/health",
                timeout=2.0,
            )
            return response.status_code == 200
        except:
            return False
