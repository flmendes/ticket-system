"""Vacancy service FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from common.config import get_settings
from common.logging import setup_logging
from .routes import router

# Initialize settings and logging
settings = get_settings()
logger = setup_logging(
    "vacancy-service",
    level=settings.log_level,
    json_logs=settings.json_logs,
)

# Create FastAPI application
app = FastAPI(
    title="Vacancy Control Service",
    description="Microservice for inventory management with atomic stock operations",
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

# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "vacancy-service",
        "version": "1.0.0",
        "status": "operational",
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"Starting Vacancy Service on port {settings.vacancy_port}")
    logger.info(f"Initial stock: {settings.initial_stock}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Vacancy Service")
