"""
Monolithic application - all services in one process.
Uses LOCAL client (direct function calls, zero network overhead).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from common.config import get_settings
from common.logging import setup_logging
from vacancy.routes import router as vacancy_router
from ticket.routes import router as ticket_router

# Initialize settings and logging
settings = get_settings()
logger = setup_logging(
    "ticket-system-monolith",
    level=settings.log_level,
    json_logs=settings.json_logs,
)


def create_app() -> FastAPI:
    """
    Create monolithic FastAPI application.

    All services run in one process with direct function calls.
    No HTTP overhead between services - maximum performance!
    """
    app = FastAPI(
        title="Ticket System (Monolith)",
        description="All services in one process with direct function calls for maximum performance",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure per environment in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include both service routers
    app.include_router(vacancy_router, tags=["vacancy"])
    app.include_router(ticket_router, tags=["tickets"])

    @app.get("/")
    async def root():
        return {
            "service": "ticket-system-monolith",
            "version": "1.0.0",
            "mode": "monolith",
            "message": "All services running in single process with direct calls",
            "performance": "Maximum - zero network overhead between services",
        }

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "mode": "monolith",
            "services": ["vacancy", "ticket"],
        }

    @app.on_event("startup")
    async def startup_event():
        """Startup event handler."""
        logger.info(f"Starting Ticket System Monolith on port {settings.monolith_port}")
        logger.info(f"Initial stock: {settings.initial_stock}")
        logger.info("Mode: MONOLITH - using direct function calls")
        logger.info("Performance: Maximum (zero network overhead)")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler."""
        logger.info("Shutting down Ticket System Monolith")

    return app


# Create app instance
app = create_app()
