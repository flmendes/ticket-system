"""Dependency injection for ticket service."""
from domain.interfaces import VacancyClient
from .services import TicketService
from .clients import create_vacancy_client


# Singleton instances
_vacancy_client: VacancyClient | None = None
_ticket_service: TicketService | None = None


def get_vacancy_client() -> VacancyClient:
    """
    Get or create vacancy client.

    Automatically selects Local or Remote based on deployment mode.
    """
    global _vacancy_client
    if _vacancy_client is None:
        _vacancy_client = create_vacancy_client()
    return _vacancy_client


def get_ticket_service() -> TicketService:
    """Get or create ticket service singleton."""
    global _ticket_service
    if _ticket_service is None:
        vacancy_client = get_vacancy_client()
        _ticket_service = TicketService(vacancy_client)
    return _ticket_service


def reset_dependencies():
    """Reset singletons (useful for testing)."""
    global _vacancy_client, _ticket_service
    _vacancy_client = None
    _ticket_service = None
