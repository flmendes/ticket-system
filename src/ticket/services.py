"""Ticket service business logic."""
from domain.interfaces import VacancyClient
from domain.exceptions import InvalidQuantityError, VacancyServiceError
from common.models import ReserveRequest


class TicketService:
    """
    Ticket purchase service.

    Orchestrates ticket purchases by coordinating with vacancy service.
    Works with any VacancyClient implementation (local or remote).

    This service is deployment-agnostic: it doesn't know or care whether
    the vacancy client uses direct calls or HTTP. This allows the same
    code to work in both monolithic and microservices modes.
    """

    def __init__(self, vacancy_client: VacancyClient):
        """
        Initialize ticket service.

        Args:
            vacancy_client: Client for communicating with vacancy service.
                          Can be LocalVacancyClient or RemoteVacancyClient.
        """
        self.vacancy_client = vacancy_client

    async def purchase(self, qty: int) -> tuple[bool, int, str]:
        """
        Purchase tickets.

        This method doesn't know or care if vacancy_client is local or remote.
        Works identically in both deployment modes.

        Args:
            qty: Quantity to purchase

        Returns:
            Tuple of (success, remaining, message)

        Raises:
            InvalidQuantityError: If quantity is invalid
            VacancyServiceError: If vacancy service fails
        """
        if qty <= 0:
            raise InvalidQuantityError(qty)

        # Reserve from vacancy service (local or remote)
        request = ReserveRequest(qty=qty)
        result = await self.vacancy_client.reserve(request)

        if result.success:
            message = "Purchase successful!"
        else:
            message = result.message or "Insufficient inventory"

        return result.success, result.remaining, message

    async def get_available(self) -> int:
        """
        Get available tickets from vacancy service.

        Returns:
            Available quantity

        Raises:
            VacancyServiceError: If vacancy service fails
        """
        result = await self.vacancy_client.get_available()
        return result.qty
