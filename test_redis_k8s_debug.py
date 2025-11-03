#!/usr/bin/env python3
"""Test Redis connection in K8s environment."""

import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from src.common.redis_client import RedisStockManager
    from src.common.config import get_settings
except ImportError:
    from common.redis_client import RedisStockManager
    from common.config import get_settings

async def test_redis_in_k8s():
    """Test Redis connectivity and operations."""
    logger.info("=== Redis Test in K8s ===")
    
    # Get settings
    settings = get_settings()
    logger.info(f"Settings redis_url: {settings.redis_url}")
    
    # Check environment
    redis_url_env = os.getenv("REDIS_URL")
    logger.info(f"REDIS_URL env var: {redis_url_env}")
    
    # Test Redis manager
    try:
        logger.info("Creating RedisStockManager...")
        manager = RedisStockManager(redis_url=settings.redis_url)
        
        logger.info("Connecting to Redis...")
        await manager.connect()
        
        logger.info("Testing Redis operations...")
        current = await manager.get_current()
        logger.info(f"Current stock: {current}")
        
        logger.info("Initializing stock...")
        await manager.initialize_stock(10000)
        
        current_after = await manager.get_current()
        logger.info(f"Stock after init: {current_after}")
        
        logger.info("✅ Redis test successful!")
        await manager.disconnect()
        
    except Exception as e:
        logger.error(f"❌ Redis test failed: {e}")
        logger.exception("Full error:")

if __name__ == "__main__":
    asyncio.run(test_redis_in_k8s())