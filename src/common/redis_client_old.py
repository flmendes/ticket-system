"""Redis client for distributed stock management."""
import asyncio
import logging
from typing import Optional
from datetime import datetime

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Fallback types for when Redis is not available
    class aioredis:
        class Redis:
            pass
        class WatchError(Exception):
            pass
        class RedisError(Exception):
            pass

from ..common.config import get_settings

logger = logging.getLogger(__name__)


class RedisStockManager:
    """
    Redis-based distributed stock manager with atomic operations.
    Prevents race conditions across multiple service instances.
    """

    def __init__(self):
        """Initialize Redis stock manager."""
        self.settings = get_settings()
        self.redis: Optional[aioredis.Redis] = None
        self.stock_key = self.settings.redis_stock_key
        self.lock_key = f"{self.stock_key}:lock"

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.redis = aioredis.from_url(
                self.settings.redis_url,
                db=self.settings.redis_db,
                max_connections=self.settings.redis_max_connections,
                socket_timeout=self.settings.redis_timeout,
                socket_connect_timeout=self.settings.redis_timeout,
                retry_on_timeout=True,
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            logger.info(f"Redis connected: {self.settings.redis_url}")
            
            # Initialize stock if not exists
            await self._initialize_stock()
            
        except RedisError as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def _initialize_stock(self) -> None:
        """Initialize stock value if it doesn't exist."""
        if not await self.redis.exists(self.stock_key):
            await self.redis.set(self.stock_key, self.settings.initial_stock)
            logger.info(f"Initialized stock: {self.settings.initial_stock}")

    async def reserve(self, qty: int) -> tuple[bool, int]:
        """
        Atomically reserve quantity using Redis transactions.

        Args:
            qty: Quantity to reserve

        Returns:
            Tuple of (success, remaining_after_operation)

        Raises:
            ValueError: If quantity is invalid
            RedisError: If Redis operation fails
        """
        if qty <= 0:
            raise ValueError(f"Quantity must be positive, got {qty}")

        if not self.redis:
            raise RedisError("Redis not connected")

        # Use Redis distributed lock for atomicity
        lock = self.redis.lock(
            self.lock_key,
            timeout=self.settings.redis_lock_timeout,
            blocking_timeout=self.settings.redis_lock_timeout
        )

        try:
            async with lock:
                # Use Redis transaction for atomic read-modify-write
                async with self.redis.pipeline(transaction=True) as pipe:
                    while True:
                        try:
                            # Watch the stock key for changes
                            await pipe.watch(self.stock_key)
                            
                            # Get current stock
                            current_stock = await self.redis.get(self.stock_key)
                            current_stock = int(current_stock) if current_stock else 0
                            
                            if current_stock >= qty:
                                # Sufficient stock - proceed with reservation
                                new_stock = current_stock - qty
                                
                                # Execute transaction
                                pipe.multi()
                                pipe.set(self.stock_key, new_stock)
                                await pipe.execute()
                                
                                logger.info(f"Reserved {qty} tickets, remaining: {new_stock}")
                                return True, new_stock
                            else:
                                # Insufficient stock
                                logger.warning(f"Insufficient stock: {current_stock} < {qty}")
                                return False, current_stock
                                
                        except aioredis.WatchError:
                            # Stock was modified by another client, retry
                            logger.debug("Stock modified during transaction, retrying...")
                            continue
                        
        except LockError:
            logger.error("Failed to acquire Redis lock for stock reservation")
            # Fallback: try to get current stock without reservation
            current_stock = await self.get_current()
            return False, current_stock

    async def get_current(self) -> int:
        """
        Get current stock value.

        Returns:
            Current stock quantity

        Raises:
            RedisError: If Redis operation fails
        """
        if not self.redis:
            raise RedisError("Redis not connected")

        try:
            stock = await self.redis.get(self.stock_key)
            return int(stock) if stock else 0
        except RedisError as e:
            logger.error(f"Failed to get current stock: {e}")
            raise

    async def set_stock(self, value: int) -> None:
        """
        Set stock value (for admin operations).

        Args:
            value: New stock value

        Raises:
            ValueError: If value is negative
            RedisError: If Redis operation fails
        """
        if value < 0:
            raise ValueError(f"Stock cannot be negative, got {value}")

        if not self.redis:
            raise RedisError("Redis not connected")

        try:
            await self.redis.set(self.stock_key, value)
            logger.info(f"Stock set to: {value}")
        except RedisError as e:
            logger.error(f"Failed to set stock: {e}")
            raise

    async def increment(self, amount: int) -> int:
        """
        Atomically increment stock (for restocking).

        Args:
            amount: Amount to add to stock

        Returns:
            New stock value

        Raises:
            RedisError: If Redis operation fails
        """
        if not self.redis:
            raise RedisError("Redis not connected")

        try:
            new_value = await self.redis.incr(self.stock_key, amount)
            logger.info(f"Stock incremented by {amount}, new value: {new_value}")
            return new_value
        except RedisError as e:
            logger.error(f"Failed to increment stock: {e}")
            raise

    async def health_check(self) -> dict:
        """
        Perform health check.

        Returns:
            Health status dictionary
        """
        try:
            if not self.redis:
                return {"status": "unhealthy", "error": "Not connected"}
            
            # Test Redis connectivity
            latency = await self.redis.ping()
            current_stock = await self.get_current()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "current_stock": current_stock,
                "ping_successful": True
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e)
            }


# Global Redis stock manager instance
redis_stock_manager = RedisStockManager()


async def get_redis_stock_manager() -> RedisStockManager:
    """
    Get Redis stock manager instance.
    
    Returns:
        Redis stock manager instance
    """
    return redis_stock_manager