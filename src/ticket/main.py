"""Ticket service FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from common.config import get_settings, DeploymentMode
from common.logging import setup_logging
from common.http_client import get_http_client, close_http_client
from .routes import router

# Initialize settings and logging
settings = get_settings()
logger = setup_logging(
    "ticket-service",
    level=settings.log_level,
    json_logs=settings.json_logs,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting Ticket Service on port {settings.ticket_port}")
    logger.info(f"Deployment mode: {settings.deployment_mode.value}")

    # Initialize HTTP client only in microservices mode
    if settings.deployment_mode == DeploymentMode.MICROSERVICES:
        logger.info(f"Vacancy service URL: {settings.vacancy_url}")
        await get_http_client()
        logger.info("HTTP client initialized with connection pooling")
    else:
        logger.info("Running in monolith mode - using direct local calls")

    yield

    # Shutdown
    logger.info("Shutting down Ticket Service")

    # Close HTTP client only if it was initialized
    if settings.deployment_mode == DeploymentMode.MICROSERVICES:
        await close_http_client()
        logger.info("HTTP client closed")


# Create FastAPI application
app = FastAPI(
    title="Ticket Sale Service",
    description="Microservice for ticket purchases with inventory coordination",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "ticket-service",
        "version": "1.0.0",
        "status": "operational",
        "deployment_mode": settings.deployment_mode.value,
        "vacancy_url": settings.vacancy_url if settings.deployment_mode == DeploymentMode.MICROSERVICES else "local",
    }
