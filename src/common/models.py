"""Shared domain models."""
from pydantic import BaseModel, Field


class ReserveRequest(BaseModel):
    """Request to reserve tickets."""
    qty: int = Field(..., gt=0, description="Quantity to reserve")


class ReserveResponse(BaseModel):
    """Response from reservation attempt."""
    success: bool
    remaining: int = Field(..., ge=0)
    message: str | None = None


class PurchaseRequest(BaseModel):
    """Request to purchase tickets."""
    qty: int = Field(..., gt=0, description="Quantity to purchase")


class PurchaseResponse(BaseModel):
    """Response from purchase attempt."""
    success: bool
    remaining: int = Field(..., ge=0)
    message: str | None = None


class AvailableResponse(BaseModel):
    """Current availability response."""
    qty: int = Field(..., ge=0, description="Available quantity")


class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str
    detail: str | None = None
    code: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    details: dict | None = None
