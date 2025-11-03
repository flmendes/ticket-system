"""Dependency injection for vacancy service."""
import os
import logging

try:
    from ..common.config import get_settings
except ImportError:
    # For standalone testing without relative imports
    from common.config import get_settings
    
from .services import HybridStockManager, VacancyService

logger = logging.getLogger(__name__)

# Global singleton - initialized once
_global_stock_manager: HybridStockManager | None = None
_global_vacancy_service: VacancyService | None = None


def create_stock_manager_sync() -> HybridStockManager:
    """Create stock manager instance synchronously."""
    settings = get_settings()
    logger.info(f"Creating stock manager with redis_url: {settings.redis_url}")
    
    return HybridStockManager(
        initial_stock=settings.initial_stock,
        redis_url=settings.redis_url,
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


async def get_stock_manager() -> HybridStockManager:
    """Get stock manager singleton - simplified version."""
    global _global_stock_manager
    
    if _global_stock_manager is None:
        logger.info("📦 Creating stock manager for the first time")
        _global_stock_manager = create_stock_manager_sync()
        logger.info("📦 Stock manager created, now initializing...")
        await _global_stock_manager.initialize()
        logger.info("📦 Stock manager created and initialized successfully")
        logger.info(f"📦 Stock manager is using Redis: {_global_stock_manager._using_redis}")
    
    return _global_stock_manager


def get_vacancy_service() -> VacancyService:
    """Get vacancy service singleton - synchronous version."""
    global _global_vacancy_service
    
    if _global_vacancy_service is None:
        logger.info("Creating vacancy service for the first time")
        # Use a simple in-memory manager for dependency injection
        # The actual manager will be set during startup
        from .services import InMemoryStockManager
        temp_manager = InMemoryStockManager(initial_stock=10000)
        _global_vacancy_service = VacancyService(temp_manager)
        logger.info("Vacancy service created with temporary manager")
    
    return _global_vacancy_service


async def update_vacancy_service_manager():
    """Update the vacancy service to use the proper stock manager."""
    global _global_vacancy_service
    
    if _global_vacancy_service:
        logger.info("🔄 Updating vacancy service stock manager...")
        old_manager_type = type(_global_vacancy_service.stock).__name__
        logger.info(f"🔄 Old manager type: {old_manager_type}")
        
        stock_manager = await get_stock_manager()
        new_manager_type = type(stock_manager).__name__
        logger.info(f"🔄 New manager type: {new_manager_type}")
        logger.info(f"🔄 New manager using Redis: {stock_manager._using_redis}")
        
        _global_vacancy_service.stock = stock_manager
        logger.info("✅ Vacancy service updated with proper stock manager")
        
        # Test the new manager
        test_current = await _global_vacancy_service.get_available()
        logger.info(f"✅ Test after update - current stock: {test_current}")
    else:
        logger.warning("⚠️ No vacancy service to update")


async def cleanup_dependencies():
    """Cleanup global dependencies during shutdown."""
    global _global_stock_manager, _global_vacancy_service
    
    logger.info("Cleaning up dependencies...")
    if _global_stock_manager:
        await _global_stock_manager.close()
        _global_stock_manager = None
    
    _global_vacancy_service = None
    logger.info("Dependencies cleaned up")
