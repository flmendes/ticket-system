"""Business exceptions (not HTTP-specific)."""


class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class InsufficientInventoryError(DomainException):
    """Raised when not enough inventory available."""

    def __init__(self, requested: int, available: int):
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient inventory: requested {requested}, available {available}"
        )


class InvalidQuantityError(DomainException):
    """Raised when quantity is invalid."""

    def __init__(self, qty: int):
        self.qty = qty
        super().__init__(f"Invalid quantity: {qty}")


class VacancyServiceError(DomainException):
    """Raised when vacancy service fails."""
    pass
