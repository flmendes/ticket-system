"""Dependency injection for vacancy service."""
from functools import lru_cache
from common.config import get_settings
from .services import StockManager, VacancyService


# Singleton instances
_stock_manager: StockManager | None = None
_vacancy_service: VacancyService | None = None


def get_stock_manager() -> StockManager:
    """Get or create stock manager singleton."""
    global _stock_manager
    if _stock_manager is None:
        settings = get_settings()
        _stock_manager = StockManager(
            initial_stock=settings.initial_stock,
            cache_ttl_seconds=settings.cache_ttl_seconds,
        )
    return _stock_manager


def get_vacancy_service() -> VacancyService:
    """Get or create vacancy service singleton."""
    global _vacancy_service
    if _vacancy_service is None:
        stock_manager = get_stock_manager()
        _vacancy_service = VacancyService(stock_manager)
    return _vacancy_service
