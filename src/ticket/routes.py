"""API routes for ticket service."""
from fastapi import APIRouter, HTTPException, Depends
from common.models import PurchaseRequest, PurchaseResponse, HealthResponse
from common.logging import setup_logging
from domain.exceptions import InvalidQuantityError, VacancyServiceError
from .services import TicketService
from .dependencies import get_ticket_service

# Setup logging
logger = setup_logging("ticket-service")

# Create router with API versioning
router = APIRouter(prefix="/api/v1", tags=["tickets"])


@router.post(
    "/purchase",
    response_model=PurchaseResponse,
    summary="Purchase tickets",
    description="Attempt to purchase a specified quantity of tickets",
    responses={
        200: {"description": "Purchase attempt completed (check success field)"},
        400: {"description": "Invalid request"},
        503: {"description": "Vacancy service unavailable"},
    },
)
async def purchase_tickets(
    request: PurchaseRequest,
    service: TicketService = Depends(get_ticket_service),
) -> PurchaseResponse:
    """
    Purchase tickets.

    Coordinates with the vacancy service to reserve inventory.
    Works in both monolithic and microservices modes.

    - **qty**: Number of tickets to purchase (must be > 0)

    Returns purchase status and remaining inventory.
    """
    try:
        logger.info(f"Purchase request: qty={request.qty}")
        success, remaining, message = await service.purchase(request.qty)

        return PurchaseResponse(
            success=success,
            remaining=remaining,
            message=message,
        )

    except InvalidQuantityError as e:
        logger.warning(f"Invalid purchase request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except VacancyServiceError as e:
        logger.error(f"Vacancy service error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Vacancy service unavailable: {str(e)}",
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the ticket service is healthy and operational",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Used by Docker, Kubernetes, and load balancers to verify service health.
    """
    return HealthResponse(status="healthy", service="ticket")


@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if the ticket service is ready to accept requests",
)
async def readiness_check(
    service: TicketService = Depends(get_ticket_service),
):
    """
    Readiness check endpoint.

    Verifies that the ticket service can communicate with dependencies.
    """
    try:
        # Try to check health of vacancy service
        is_ready = await service.vacancy_client.health_check()

        if is_ready:
            return {
                "status": "ready",
                "service": "ticket",
                "dependencies": {"vacancy": "healthy"},
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Vacancy service not healthy",
            )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}",
        )
