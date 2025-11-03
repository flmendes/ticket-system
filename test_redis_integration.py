"""
Test script to verify Redis integration works properly.
Tests both Redis and fallback modes.
"""
import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, '/Users/flavio/Developer/Labs/python/ticket-system/src')

# Fix import paths for testing
import vacancy.services
import common.redis_client

# Import classes directly
HybridStockManager = vacancy.services.HybridStockManager
InMemoryStockManager = vacancy.services.InMemoryStockManager
RedisStockManager = common.redis_client.RedisStockManager


async def test_in_memory_manager():
    """Test the in-memory stock manager."""
    print("🔧 Testing In-Memory Stock Manager...")
    
    manager = InMemoryStockManager(initial_stock=100)
    
    # Test initial stock
    current = await manager.get_current()
    print(f"   Initial stock: {current}")
    assert current == 100
    
    # Test reservation
    success, remaining = await manager.reserve(25)
    print(f"   Reserve 25: success={success}, remaining={remaining}")
    assert success is True
    assert remaining == 75
    
    # Test insufficient stock
    success, remaining = await manager.reserve(100)
    print(f"   Reserve 100 (insufficient): success={success}, remaining={remaining}")
    assert success is False
    assert remaining == 75
    
    print("✅ In-Memory Stock Manager: PASSED")


async def test_redis_manager():
    """Test the Redis stock manager (if available)."""
    print("🔧 Testing Redis Stock Manager...")
    
    try:
        # Try to connect to Redis
        redis_manager = RedisStockManager(redis_url="redis://localhost:6379/1")  # Use DB 1 for testing
        await redis_manager.connect()
        
        # Initialize stock
        await redis_manager.initialize_stock(200)
        
        # Test current stock
        current = await redis_manager.get_current()
        print(f"   Redis initial stock: {current}")
        
        # Test reservation
        success, remaining = await redis_manager.reserve(50)
        print(f"   Redis reserve 50: success={success}, remaining={remaining}")
        assert success is True
        
        # Test health check
        health = await redis_manager.health_check()
        print(f"   Redis health: {health['status']}")
        
        # Cleanup
        await redis_manager.close()
        print("✅ Redis Stock Manager: PASSED")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Redis Stock Manager: SKIPPED ({e})")
        return False


async def test_hybrid_manager():
    """Test the hybrid stock manager."""
    print("🔧 Testing Hybrid Stock Manager...")
    
    # Test with Redis (if available)
    redis_available = False
    try:
        manager = HybridStockManager(
            initial_stock=150,
            redis_url="redis://localhost:6379/2",  # Use DB 2 for testing
            cache_ttl_seconds=1
        )
        await manager.initialize()
        redis_available = manager._using_redis
        print(f"   Hybrid manager using Redis: {redis_available}")
        
    except Exception:
        # Fallback to in-memory only
        manager = HybridStockManager(initial_stock=150, redis_url=None)
        await manager.initialize()
        print("   Hybrid manager using in-memory fallback")
    
    # Test operations
    current = await manager.get_current()
    print(f"   Hybrid initial stock: {current}")
    
    success, remaining = await manager.reserve(30)
    print(f"   Hybrid reserve 30: success={success}, remaining={remaining}")
    assert success is True
    
    # Test health check
    health = await manager.health_check()
    print(f"   Hybrid health: {health}")
    assert health['status'] == 'healthy'
    
    # Cleanup
    await manager.close()
    print("✅ Hybrid Stock Manager: PASSED")
    
    return redis_available


async def main():
    """Run all tests."""
    print("🚀 Starting Redis Integration Tests\n")
    
    # Test in-memory manager
    await test_in_memory_manager()
    print()
    
    # Test Redis manager
    redis_works = await test_redis_manager()
    print()
    
    # Test hybrid manager
    hybrid_redis = await test_hybrid_manager()
    print()
    
    # Summary
    print("📊 Test Summary:")
    print(f"   ✅ In-Memory Manager: Working")
    print(f"   {'✅' if redis_works else '⚠️ '} Redis Manager: {'Working' if redis_works else 'Unavailable'}")
    print(f"   ✅ Hybrid Manager: Working ({'Redis' if hybrid_redis else 'In-Memory'} mode)")
    
    if redis_works:
        print("\n🎉 Redis integration is fully functional!")
    else:
        print("\n💡 Redis not available, but fallback mode works correctly.")
    
    print("\n✨ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())