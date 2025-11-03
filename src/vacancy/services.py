"""Vacancy service business logic."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from common.redis_client import RedisStockManager
else:
    try:
        from ..common.redis_client import RedisStockManager
    except ImportError:
        # For standalone testing without relative imports
        from common.redis_client import RedisStockManager

logger = logging.getLogger(__name__)


class InMemoryStockManager:
    """
    Thread-safe in-memory stock management with caching.
    Implements atomic operations to prevent race conditions.
    Used as fallback when Redis is unavailable.
    """

    def __init__(self, initial_stock: int, cache_ttl_seconds: int = 1):
        """
        Initialize stock manager.

        Args:
            initial_stock: Initial inventory quantity
            cache_ttl_seconds: Cache TTL for read operations
        """
        self.total = initial_stock
        self.lock = asyncio.Lock()
        self._cached_total: Optional[int] = None
        self._cache_expiry: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=cache_ttl_seconds)

    async def reserve(self, qty: int) -> tuple[bool, int]:
        """
        Attempt to reserve quantity.

        Args:
            qty: Quantity to reserve

        Returns:
            Tuple of (success, remaining_after_operation)

        Raises:
            ValueError: If quantity is invalid
        """
        if qty <= 0:
            raise ValueError(f"Quantity must be positive, got {qty}")

        async with self.lock:
            if self.total >= qty:
                self.total -= qty
                self._invalidate_cache()
                return True, self.total
            return False, self.total

    async def get_current(self, use_cache: bool = True) -> int:
        """
        Get current inventory.

        Args:
            use_cache: Whether to use cached value

        Returns:
            Current inventory quantity
        """
        if use_cache and self._is_cache_valid():
            return self._cached_total

        async with self.lock:
            self._update_cache()
            return self.total

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        return (
            self._cache_expiry is not None
            and datetime.now() < self._cache_expiry
        )

    def _update_cache(self) -> None:
        """Update cache with current value."""
        self._cached_total = self.total
        self._cache_expiry = datetime.now() + self._cache_ttl

    def _invalidate_cache(self) -> None:
        """Invalidate cache after write."""
        self._cache_expiry = None


class HybridStockManager:
    """
    Hybrid stock manager that uses Redis as primary and in-memory as fallback.
    Provides distributed atomic operations with high availability.
    """

    def __init__(self, initial_stock: int, redis_url: Optional[str] = None, cache_ttl_seconds: int = 1):
        """
        Initialize hybrid stock manager.

        Args:
            initial_stock: Initial inventory quantity
            redis_url: Redis connection URL (if None, uses in-memory only)
            cache_ttl_seconds: Cache TTL for read operations
        """
        self.initial_stock = initial_stock
        self.redis_url = redis_url
        self.redis_manager: Optional[RedisStockManager] = None
        self.fallback_manager = InMemoryStockManager(initial_stock, cache_ttl_seconds)
        self._using_redis = False

    async def initialize(self) -> None:
        """Initialize the stock manager and determine which backend to use."""
        logger.info(f"🔧 HybridStockManager.initialize() called with redis_url: {self.redis_url}")
        
        if self.redis_url:
            # Retry logic for Kubernetes environment
            max_retries = 5
            retry_delay = 2  # seconds
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"📡 Attempt {attempt}/{max_retries}: Creating RedisStockManager...")
                    self.redis_manager = RedisStockManager(redis_url=self.redis_url)
                    
                    logger.info(f"📡 Attempt {attempt}/{max_retries}: Connecting to Redis...")
                    await self.redis_manager.connect()
                    
                    logger.info(f"📡 Attempt {attempt}/{max_retries}: Testing Redis connection...")
                    await self.redis_manager.redis.ping()
                    
                    logger.info(f"📡 Attempt {attempt}/{max_retries}: Initializing Redis stock with {self.initial_stock}...")
                    await self.redis_manager.initialize_stock(self.initial_stock)
                    
                    # Verify Redis is working
                    current_redis = await self.redis_manager.get_current()
                    logger.info(f"✅ Redis connection successful! Current stock: {current_redis}")
                    
                    self._using_redis = True
                    logger.info("✅ HybridStockManager initialized with Redis backend")
                    return  # Success, exit retry loop
                    
                except Exception as e:
                    logger.warning(f"❌ Attempt {attempt}/{max_retries} failed: {e}")
                    if attempt < max_retries:
                        logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                    else:
                        logger.error(f"❌ All {max_retries} Redis connection attempts failed")
                        logger.exception("Final Redis initialization error:")
            
            # If we get here, all retries failed
            logger.warning("❌ Redis initialization failed after all retries, using in-memory fallback")
            self._using_redis = False
        else:
            logger.info("ℹ️ No Redis URL provided, using in-memory backend")
            self._using_redis = False

    async def reserve(self, qty: int) -> tuple[bool, int]:
        """
        Attempt to reserve quantity using Redis or fallback.

        Args:
            qty: Quantity to reserve

        Returns:
            Tuple of (success, remaining_after_operation)
        """
        logger.info(f"HybridStockManager.reserve() called: qty={qty}, using_redis={self._using_redis}")
        
        if self._using_redis and self.redis_manager:
            try:
                logger.info("Using Redis for reserve operation")
                result = await self.redis_manager.reserve(qty)
                logger.info(f"Redis reserve result: {result}")
                return result
            except Exception as e:
                logger.error(f"Redis reserve failed, falling back to in-memory: {e}")
                self._using_redis = False
                # Sync fallback manager with last known Redis state if possible
                try:
                    current_redis = await self.redis_manager.get_current()
                    self.fallback_manager.total = current_redis
                except Exception:
                    pass
        
        logger.info("Using in-memory fallback for reserve operation")
        result = await self.fallback_manager.reserve(qty)
        logger.info(f"In-memory reserve result: {result}")
        return result

    async def get_current(self, use_cache: bool = True) -> int:
        """
        Get current inventory using Redis or fallback.

        Args:
            use_cache: Whether to use cached value

        Returns:
            Current inventory quantity
        """
        logger.info(f"HybridStockManager.get_current() called: use_cache={use_cache}, using_redis={self._using_redis}")
        
        if self._using_redis and self.redis_manager:
            try:
                logger.info("Using Redis for get_current operation")
                result = await self.redis_manager.get_current(use_cache)
                logger.info(f"Redis get_current result: {result}")
                return result
            except Exception as e:
                logger.error(f"Redis get_current failed, falling back to in-memory: {e}")
                self._using_redis = False
        
        logger.info("Using in-memory fallback for get_current operation")
        result = await self.fallback_manager.get_current(use_cache)
        logger.info(f"In-memory get_current result: {result}")
        return result

    async def health_check(self) -> dict:
        """
        Get health status of the stock manager.

        Returns:
            Health status dictionary
        """
        status = {
            "status": "healthy",
            "backend": "redis" if self._using_redis else "in-memory",
            "current_stock": await self.get_current()
        }

        if self.redis_manager:
            try:
                redis_health = await self.redis_manager.health_check()
                status["redis_status"] = redis_health
            except Exception as e:
                status["redis_status"] = {"status": "unhealthy", "error": str(e)}
        
        return status

    async def close(self) -> None:
        """Close connections and cleanup resources."""
        if self.redis_manager:
            try:
                await self.redis_manager.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")


class VacancyService:
    """Vacancy service - handles inventory operations."""

    def __init__(self, stock_manager: Union[HybridStockManager, InMemoryStockManager]):
        """
        Initialize vacancy service.

        Args:
            stock_manager: Stock manager instance (hybrid or in-memory)
        """
        self.stock = stock_manager

    async def reserve(self, qty: int) -> tuple[bool, int, str]:
        """
        Reserve tickets.

        Args:
            qty: Quantity to reserve

        Returns:
            Tuple of (success, remaining, message)

        Raises:
            ValueError: If quantity is invalid
        """
        success, remaining = await self.stock.reserve(qty)

        if success:
            message = f"Reserved {qty} tickets"
        else:
            message = "Insufficient inventory"

        return success, remaining, message

    async def get_available(self) -> int:
        """
        Get available inventory.

        Returns:
            Available quantity
        """
        return await self.stock.get_current()

    async def health_check(self) -> dict:
        """
        Get service health status.

        Returns:
            Health status dictionary
        """
        if hasattr(self.stock, 'health_check'):
            return await self.stock.health_check()
        else:
            current_stock = await self.get_available()
            return {
                "status": "healthy",
                "stock_manager_type": "in-memory",
                "current_stock": current_stock
            }
