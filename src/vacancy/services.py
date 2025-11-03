"""Vacancy service business logic."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional


class StockManager:
    """
    Thread-safe stock management with caching.
    Implements atomic operations to prevent race conditions.
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


class VacancyService:
    """Vacancy service - handles inventory operations."""

    def __init__(self, stock_manager: StockManager):
        """
        Initialize vacancy service.

        Args:
            stock_manager: Stock manager instance
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
