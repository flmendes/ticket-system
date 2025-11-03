"""API routes for vacancy service."""
from fastapi import APIRouter, HTTPException, Depends
from common.models import ReserveRequest, ReserveResponse, AvailableResponse, HealthResponse
from common.logging import setup_logging
from .services import VacancyService
from .dependencies import get_vacancy_service

# Setup logging
logger = setup_logging("vacancy-service")

# Create router with API versioning
router = APIRouter(prefix="/api/v1", tags=["vacancy"])


@router.post(
    "/reserve",
    response_model=ReserveResponse,
    summary="Reserve tickets",
    description="Attempt to reserve a specified quantity of tickets from inventory",
)
async def reserve_tickets(
    request: ReserveRequest,
    service: VacancyService = Depends(get_vacancy_service),
) -> ReserveResponse:
    """
    Reserve tickets from inventory.

    - **qty**: Number of tickets to reserve (must be > 0)

    Returns reservation status and remaining inventory.
    """
    try:
        logger.info(f"Reserve request: qty={request.qty}")
        success, remaining, message = await service.reserve(request.qty)

        return ReserveResponse(
            success=success,
            remaining=remaining,
            message=message,
        )

    except ValueError as e:
        logger.warning(f"Invalid reservation request: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/available",
    response_model=AvailableResponse,
    summary="Get available inventory",
    description="Retrieve the current number of available tickets",
)
async def get_available(
    service: VacancyService = Depends(get_vacancy_service),
) -> AvailableResponse:
    """
    Get available inventory.

    Returns the current number of tickets available for reservation.
    """
    qty = await service.get_available()
    logger.debug(f"Available inventory: {qty}")
    return AvailableResponse(qty=qty)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the vacancy service is healthy and operational",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Used by Docker, Kubernetes, and load balancers to verify service health.
    """
    return HealthResponse(status="healthy", service="vacancy")
