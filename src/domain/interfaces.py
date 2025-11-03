"""
Domain interfaces using Python's Protocol (structural typing).
Both local and remote implementations must satisfy these contracts.
"""
from typing import Protocol, runtime_checkable
from common.models import ReserveRequest, ReserveResponse, AvailableResponse


@runtime_checkable
class VacancyClient(Protocol):
    """
    Interface for vacancy service communication.
    Can be implemented as local (direct calls) or remote (HTTP).

    This allows the ticket service to work identically in both
    monolithic and microservices deployment modes.
    """

    async def reserve(self, request: ReserveRequest) -> ReserveResponse:
        """
        Reserve tickets.

        Args:
            request: Reservation request with quantity

        Returns:
            Reservation response with success status and remaining inventory
        """
        ...

    async def get_available(self) -> AvailableResponse:
        """
        Get available inventory.

        Returns:
            Available response with quantity
        """
        ...

    async def health_check(self) -> bool:
        """
        Check if vacancy service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        ...
