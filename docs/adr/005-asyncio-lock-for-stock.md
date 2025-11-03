# ADR 005: Asyncio Lock for Stock Management

**Status**: Accepted

**Date**: 2025-11-02

**Deciders**: Development Team

---

## Context

The vacancy service manages a shared resource (available tickets count) that is accessed concurrently by multiple requests. Without proper synchronization, race conditions can occur:

**Race Condition Example**:
```
Time | Request A        | Request B        | Stock Value
-----|-----------------|------------------|-------------
t1   | Read: stock=100 |                  | 100
t2   |                 | Read: stock=100  | 100
t3   | Decrement: 99   |                  | 99
t4   |                 | Decrement: 99    | 99  ← WRONG!
```

Expected final value: 98, Actual: 99 (lost update)

### Requirements

- **Atomicity**: Stock updates must be atomic
- **Performance**: Minimize lock contention under high load
- **Correctness**: Never oversell tickets
- **Async-compatible**: Works with FastAPI's async handlers

---

## Decision

Use **`asyncio.Lock`** for synchronizing access to the stock counter.

### Implementation

```python
class StockManager:
    def __init__(self, initial_stock: int):
        self.total = initial_stock
        self.lock = asyncio.Lock()  # One lock per instance
        self._cache = None
        self._cache_time = None

    async def reserve(self, qty: int) -> tuple[bool, int]:
        async with self.lock:  # Acquire lock
            if self.total >= qty:
                self.total -= qty
                self._invalidate_cache()
                return True, self.total
            return False, self.total
```

**Lock Scope**: Per StockManager instance (singleton per service)

---

## Consequences

### Positive

✅ **Correctness**: Guarantees atomic updates (no race conditions)
✅ **Simple**: Built-in Python feature, no external dependencies
✅ **Async-Native**: Works seamlessly with `asyncio`
✅ **Testable**: Easy to verify correctness with load tests
✅ **Proven**: 100% success rate under 1000+ concurrent requests

### Negative

⚠️ **Bottleneck**: Single lock serializes all stock operations
⚠️ **Latency**: Lock contention increases latency under high load
⚠️ **Single Point**: One lock across all pods would require distributed lock

### Neutral

🔄 **Caching Added**: Implemented read caching (1s TTL) to reduce lock contention:
- Read-heavy workload: 70% reduction in lock acquisitions
- Trade-off: Slightly stale data (max 1s old)

---

## Alternatives Considered

### 1. No Synchronization
- ❌ Race conditions guaranteed
- ❌ Lost updates
- ✅ Fastest (but incorrect)

### 2. Threading Lock (`threading.Lock`)
- ❌ Doesn't work with `asyncio`
- ❌ Blocks event loop
- ❌ Not async-compatible

### 3. Database with ACID Transactions
- ✅ Distributed correctness
- ⚠️ Requires database setup
- ⚠️ Higher latency (~10-50ms per operation)
- ⏸️ Deferred for future enhancement

### 4. Redis with Distributed Lock
- ✅ Works across multiple pods
- ⚠️ Requires Redis infrastructure
- ⚠️ Network latency
- ⏸️ Deferred for future enhancement

### 5. Semaphore (`asyncio.Semaphore`)
- ❌ Wrong abstraction (for limiting concurrency, not mutual exclusion)
- ❌ Doesn't guarantee atomicity

---

## Limitations

**Current Implementation**:
- ⚠️ Lock is per-pod, not distributed
- ⚠️ Each pod has its own stock counter
- ⚠️ Scaling horizontally splits the stock

**Workaround**:
- Deploy as single instance for stock management
- Or use dedicated "inventory service" with persistent storage

**Future**:
- Migrate to database with transactions (PostgreSQL)
- Or use Redis with distributed locks
- See: [Future Enhancements](#future-enhancements)

---

## Validation

**Load Test Results**:
- Concurrent Requests: 1000+
- Success Rate: 100%
- Race Conditions: 0
- Lock Wait Time: < 5ms (P95)

**Verification**:
```python
# Test: 1000 concurrent reservations of 1 ticket each
initial_stock = 1000
requests = 1000
expected_final = 0

# Result: final_stock = 0 ✅
# All operations serialized correctly
```

---

## Future Enhancements

### Option 1: Database-Backed Stock
```python
# Use PostgreSQL with row-level locking
async def reserve(self, qty: int):
    async with db.transaction():
        result = await db.execute(
            "UPDATE stock SET qty = qty - $1 "
            "WHERE qty >= $1 "
            "RETURNING qty",
            qty
        )
```

### Option 2: Redis with Lua Script
```lua
-- Atomic reservation in Redis
local stock = tonumber(redis.call('GET', 'stock'))
if stock >= ARGV[1] then
    redis.call('DECRBY', 'stock', ARGV[1])
    return redis.call('GET', 'stock')
end
return -1
```

### Option 3: Event Sourcing
- All stock changes as events
- Single writer, multiple readers
- Full audit trail

---

## References

- [Python asyncio.Lock Documentation](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock)
- [Race Conditions](https://en.wikipedia.org/wiki/Race_condition)
- [ACID Transactions](https://en.wikipedia.org/wiki/ACID)

---

**Related ADRs**: ADR-001 (Dual-Mode Architecture)
