"""Vacancy service FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# For standalone execution without relative imports
from common.config import get_settings
from common.logging import setup_logging

from .routes import router
from .dependencies import cleanup_dependencies, get_stock_manager, update_vacancy_service_manager

# Initialize settings and logging
settings = get_settings()
logger = setup_logging(
    "vacancy-service",
    level=settings.log_level,
    json_logs=settings.json_logs,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info(f"Starting Vacancy Service on port {settings.vacancy_port}")
    logger.info(f"Initial stock: {settings.initial_stock}")
    
    # Redis configuration and pre-flight check
    import os
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        logger.info(f"📡 Redis URL configured: {redis_url}")
        
        # Pre-flight Redis connectivity check
        try:
            logger.info("🔍 Pre-flight Redis connectivity check...")
            import redis.asyncio as aioredis
            test_redis = aioredis.from_url(redis_url, socket_connect_timeout=5)
            await test_redis.ping()
            await test_redis.close()
            logger.info("✅ Pre-flight Redis check successful")
        except Exception as e:
            logger.warning(f"⚠️ Pre-flight Redis check failed: {e}")
            logger.warning("🔄 Will retry during stock manager initialization...")
    else:
        logger.info("ℹ️ No Redis URL configured, using in-memory stock management")
    
    # Initialize stock manager during startup to avoid lazy loading issues
    try:
        logger.info("🚀 Initializing stock manager during startup...")
        stock_manager = await get_stock_manager()
        logger.info("✅ Stock manager initialization completed successfully")
        
        # Create vacancy service first
        logger.info("📦 Creating vacancy service...")
        from .dependencies import get_vacancy_service
        vacancy_service = get_vacancy_service()  # This creates the service with temp manager
        logger.info("✅ Vacancy service created")
        
        # Now update vacancy service to use the proper manager
        await update_vacancy_service_manager()
        logger.info("Vacancy service updated with proper stock manager")
        
        # Test a basic operation to ensure everything is working
        current_stock = await stock_manager.get_current()
        logger.info(f"Current stock after initialization: {current_stock}")
        
        # Test through vacancy service to confirm it's working
        vacancy_stock = await vacancy_service.get_available()
        logger.info(f"Stock through vacancy service: {vacancy_stock}")
        
    except Exception as e:
        logger.error(f"Failed to initialize stock manager: {e}")
        logger.exception("Stock manager initialization error:")
        # Continue with startup, will fallback to in-memory
    
    yield
    
    # Shutdown
    logger.info("Shutting down Vacancy Service")
    await cleanup_dependencies()


# Create FastAPI application
app = FastAPI(
    title="Vacancy Control Service",
    description="Microservice for inventory management with atomic stock operations and Redis integration",
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
        "service": "vacancy-service",
        "version": "1.0.0",
        "status": "operational",
        "description": "Distributed stock management with Redis integration",
    }
