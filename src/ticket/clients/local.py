"""
Local implementation of VacancyClient.
Makes direct function calls - NO HTTP overhead.
Used in monolithic mode.
"""
from common.models import ReserveRequest, ReserveResponse, AvailableResponse
from domain.interfaces import VacancyClient
from domain.exceptions import InvalidQuantityError
from vacancy.services import VacancyService
from vacancy.dependencies import get_vacancy_service


class LocalVacancyClient:
    """
    Local vacancy client - direct function calls.
    Zero network overhead, perfect for monolithic deployment.

    This implementation calls the VacancyService directly without
    any HTTP layer, making it extremely fast (microseconds vs milliseconds).
    """

    def __init__(self, vacancy_service: VacancyService | None = None):
        """
        Initialize local client.

        Args:
            vacancy_service: Optional VacancyService instance.
                           If None, will get from dependency injection.
        """
        self._service = vacancy_service or get_vacancy_service()

    async def reserve(self, request: ReserveRequest) -> ReserveResponse:
        """
        Reserve tickets via direct call.

        This bypasses all HTTP overhead and calls the service directly.

        Args:
            request: Reservation request

        Returns:
            Reservation response

        Raises:
            InvalidQuantityError: If quantity is invalid
        """
        try:
            success, remaining, message = await self._service.reserve(request.qty)

            return ReserveResponse(
                success=success,
                remaining=remaining,
                message=message,
            )

        except ValueError as e:
            raise InvalidQuantityError(request.qty) from e

    async def get_available(self) -> AvailableResponse:
        """
        Get available inventory via direct call.

        Returns:
            Available response
        """
        qty = await self._service.get_available()
        return AvailableResponse(qty=qty)

    async def health_check(self) -> bool:
        """
        Health check via direct call.

        Returns:
            Always True for local client (no network to fail)
        """
        # Local client is always "healthy" since there's no network
        return True
