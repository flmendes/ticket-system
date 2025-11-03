"""
Client implementations for vacancy service communication.

Factory for creating appropriate vacancy client based on configuration.
"""
from domain.interfaces import VacancyClient
from common.config import get_settings, DeploymentMode
from .local import LocalVacancyClient
from .remote import RemoteVacancyClient


def create_vacancy_client() -> VacancyClient:
    """
    Factory: Create appropriate vacancy client based on deployment mode.

    Returns:
        LocalVacancyClient in monolithic mode (direct calls, zero network overhead)
        RemoteVacancyClient in microservices mode (HTTP calls)
    """
    settings = get_settings()

    if settings.deployment_mode == DeploymentMode.MONOLITH:
        return LocalVacancyClient()
    else:
        return RemoteVacancyClient()
