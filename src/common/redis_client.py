"""Redis-based distributed stock management with atomic operations."""
import asyncio
import logging
import random
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

logger = logging.getLogger(__name__)


class RedisStockManager:
    """
    Redis-based distributed stock manager with atomic operations.
    Uses Redis transactions and locks to ensure data consistency across multiple instances.
    """

    def __init__(self, redis_url: str):
        """
        Initialize Redis stock manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.stock_key = "ticket_stock"
        self.lock_key = "ticket_stock_lock"
        self.lock_timeout = 5  # seconds - Reduced for faster lock turnover
        self._connected = False

    async def connect(self) -> None:
        """Establish Redis connection with Kubernetes-optimized settings."""
        try:
            logger.info(f"🔗 Connecting to Redis at: {self.redis_url}")
            
            self.redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=10,  # Increased for K8s
                socket_timeout=10,          # Increased for K8s
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
                health_check_interval=30,
                max_connections=20,
                # Kubernetes-specific optimizations
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # Test connection with retry
            logger.info("🔍 Testing Redis connection...")
            await self.redis.ping()
            self._connected = True
            logger.info(f"✅ Successfully connected to Redis: {self.redis_url}")
            
        except Exception as e:
            self._connected = False
            logger.error(f"❌ Failed to connect to Redis: {e}")
            logger.error(f"❌ Redis URL: {self.redis_url}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            try:
                await self.redis.close()
                logger.info("Disconnected from Redis")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}")
            finally:
                self._connected = False

    async def close(self) -> None:
        """Alias for disconnect for consistency."""
        await self.disconnect()

    async def initialize_stock(self, initial_value: int) -> None:
        """
        Initialize stock value if not exists.

        Args:
            initial_value: Initial stock quantity
        """
        if not self._connected or not self.redis:
            raise ConnectionError("Redis not connected")

        # Use SET NX to only set if key doesn't exist
        was_set = await self.redis.set(self.stock_key, initial_value, nx=True)
        if was_set:
            logger.info(f"Initialized Redis stock to {initial_value}")
        else:
            current = await self.redis.get(self.stock_key)
            logger.info(f"Redis stock already exists: {current}")

    async def reserve(self, qty: int) -> tuple[bool, int]:
        """
        Atomically reserve quantity using Redis transactions.

        Args:
            qty: Quantity to reserve

        Returns:
            Tuple of (success, remaining_after_operation)

        Raises:
            ValueError: If quantity is invalid
            ConnectionError: If Redis is not connected
        """
        if qty <= 0:
            raise ValueError(f"Quantity must be positive, got {qty}")

        if not self._connected or not self.redis:
            raise ConnectionError("Redis not connected")

        # Use distributed lock to ensure atomicity across multiple instances
        lock_acquired = False
        max_retries = 5  # Increased retries for high-concurrency scenarios
        try:
            # Try to acquire distributed lock with exponential backoff
            for attempt in range(max_retries):
                lock_acquired = await self.redis.set(
                    self.lock_key, 
                    f"locked_by_{id(self)}_{datetime.now().isoformat()}", 
                    nx=True, 
                    ex=self.lock_timeout
                )
                
                if lock_acquired:
                    break
                    
                # Shorter exponential backoff for faster lock turnover
                if attempt < max_retries - 1:
                    wait_time = (0.01 * (2 ** attempt)) + (random.random() * 0.01)
                    await asyncio.sleep(wait_time)

            if not lock_acquired:
                raise RuntimeError("Could not acquire distributed lock for stock reservation")

            # Perform atomic transaction
            async with self.redis.pipeline(transaction=True) as pipe:
                while True:
                    try:
                        # Watch the stock key for changes
                        await pipe.watch(self.stock_key)
                        
                        # Get current stock OUTSIDE pipeline (before multi())
                        current_stock = await self.redis.get(self.stock_key)
                        if current_stock is None:
                            current_stock = 0
                        else:
                            current_stock = int(current_stock)

                        # Check if reservation is possible
                        if current_stock >= qty:
                            # Start transaction
                            pipe.multi()
                            new_stock = current_stock - qty
                            pipe.set(self.stock_key, new_stock)
                            
                            # Execute transaction
                            result = await pipe.execute()
                            logger.info(f"Redis reserve successful: {current_stock} -> {new_stock} (qty={qty})")
                            return True, new_stock
                        else:
                            # Insufficient stock
                            logger.warning(f"Insufficient stock for reservation: {current_stock} < {qty}")
                            return False, current_stock

                    except aioredis.WatchError:
                        # Key was modified during transaction, retry
                        logger.debug("Redis transaction conflict, retrying...")
                        continue
                    except Exception as e:
                        logger.error(f"Redis reserve transaction error: {e}")
                        raise

        finally:
            if lock_acquired and self.redis:
                # Release distributed lock
                try:
                    await self.redis.delete(self.lock_key)
                except Exception as e:
                    logger.warning(f"Failed to release distributed lock: {e}")

    async def get_current(self, use_cache: bool = True) -> int:
        """
        Get current stock value.

        Args:
            use_cache: Unused for Redis (always fetches latest)

        Returns:
            Current stock quantity

        Raises:
            ConnectionError: If Redis is not connected
        """
        if not self._connected or not self.redis:
            raise ConnectionError("Redis not connected")

        try:
            stock = await self.redis.get(self.stock_key)
            return int(stock) if stock is not None else 0
        except Exception as e:
            logger.error(f"Failed to get stock from Redis: {e}")
            raise

    async def health_check(self) -> dict:
        """
        Perform health check on Redis connection.

        Returns:
            Health status dictionary
        """
        status = {
            "status": "healthy" if self._connected else "unhealthy",
            "redis_connected": self._connected,
            "redis_url": self.redis_url.split('@')[-1] if '@' in self.redis_url else self.redis_url,  # Hide auth
        }

        if self._connected and self.redis:
            try:
                # Test Redis operations
                await self.redis.ping()
                current_stock = await self.get_current()
                status.update({
                    "redis_ping": "ok",
                    "current_stock": current_stock,
                })
            except Exception as e:
                status.update({
                    "status": "unhealthy",
                    "redis_ping": "failed",
                    "error": str(e),
                })

        return status