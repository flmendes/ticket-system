#!/usr/bin/env python3
"""Test Redis connection and operations directly."""

import asyncio
import os
import sys
sys.path.insert(0, '/app/src')

from common.redis_client import RedisStockManager

async def test_redis_directly():
    """Test Redis operations directly."""
    print("=== Direct Redis Test ===")
    
    # Use the same URL as the service
    redis_url = "redis://redis:6379/0"
    print(f"Testing Redis URL: {redis_url}")
    
    try:
        # Create manager
        manager = RedisStockManager(redis_url=redis_url)
        print("✅ RedisStockManager created")
        
        # Connect
        await manager.connect()
        print("✅ Connected to Redis")
        
        # Check current stock
        try:
            current = await manager.get_current()
            print(f"📊 Current stock: {current}")
        except Exception as e:
            print(f"❌ Error getting current stock: {e}")
        
        # Initialize stock
        await manager.initialize_stock(10000)
        print("✅ Stock initialized")
        
        # Check again
        current = await manager.get_current()
        print(f"📊 Stock after init: {current}")
        
        # Test reserve
        success, remaining = await manager.reserve(5)
        print(f"📝 Reserve 5: success={success}, remaining={remaining}")
        
        # Check final
        current = await manager.get_current()
        print(f"📊 Final stock: {current}")
        
        # Disconnect
        await manager.disconnect()
        print("✅ Disconnected")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis_directly())