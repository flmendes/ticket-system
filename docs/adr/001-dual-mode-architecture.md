# ADR 001: Dual-Mode Architecture (Monolith + Microservices)

**Status**: Accepted

**Date**: 2025-11-02

**Deciders**: Development Team

---

## Context

The system needs to support different deployment scenarios:
- **Development**: Fast iteration, easy debugging, minimal infrastructure
- **Production**: Scalability, fault isolation, independent service deployment

Traditional approaches force choosing between monolith OR microservices architecture, requiring different codebases or significant refactoring when transitioning.

### Problem

- Developers want fast local development without managing multiple services
- Production needs horizontal scalability and fault isolation
- Maintaining two separate codebases (monolith + microservices) is expensive
- Migrating from monolith to microservices later is risky and time-consuming

---

## Decision

Implement a **dual-mode architecture** where the same codebase can run as:

1. **Monolith Mode**: All services in a single process with direct function calls
2. **Microservices Mode**: Services as independent processes with HTTP communication

### Implementation

**Architecture Pattern**: Strategy Pattern + Dependency Injection

```python
# Domain layer defines interface
class VacancyClient(Protocol):
    async def reserve(self, request: ReserveRequest) -> ReserveResponse
    async def get_available(self) -> AvailableResponse

# Two implementations
class LocalVacancyClient:   # Direct calls (monolith)
class RemoteVacancyClient:  # HTTP calls (microservices)

# Factory selects based on DEPLOYMENT_MODE
def create_vacancy_client() -> VacancyClient:
    if settings.deployment_mode == DeploymentMode.MONOLITH:
        return LocalVacancyClient()
    else:
        return RemoteVacancyClient()
```

**Configuration**:
- Environment variable `DEPLOYMENT_MODE` controls the mode
- Default: `microservices` (safer for production)
- No code changes needed to switch modes

---

## Consequences

### Positive

✅ **Same Codebase**: Single codebase for both modes
✅ **Fast Development**: Monolith mode for local dev (15x faster)
✅ **Scalable Production**: Microservices mode for production
✅ **Easy Migration**: Switch modes with one environment variable
✅ **Type Safety**: Protocol ensures both implementations are compatible
✅ **Testing**: Can test both modes with same tests

### Negative

⚠️ **Complexity**: More abstraction layers (protocols, factories)
⚠️ **Discipline Required**: Developers must maintain both paths
⚠️ **Interface Constraints**: All communication must go through defined interfaces

### Neutral

🔄 **Performance Trade-off**:
- Monolith: ~2ms latency (direct calls)
- Microservices: ~20ms latency (HTTP overhead)
- Both acceptable for our use case

---

## Alternatives Considered

### 1. Monolith Only
- ❌ Doesn't scale horizontally
- ❌ All or nothing deployment
- ✅ Simple

### 2. Microservices Only
- ❌ Complex local development
- ❌ Slow iteration
- ✅ Scalable

### 3. Separate Codebases
- ❌ Double maintenance
- ❌ Feature parity issues
- ❌ Migration complexity

---

## Implementation Details

**Files**:
- `src/domain/interfaces.py` - Protocol definitions
- `src/ticket/clients/local.py` - Monolith implementation
- `src/ticket/clients/remote.py` - Microservices implementation
- `src/ticket/clients/__init__.py` - Factory
- `src/apps/monolith.py` - Monolith application

**Configuration**:
```bash
# Monolith
DEPLOYMENT_MODE=monolith python scripts/run_monolith.py

# Microservices
DEPLOYMENT_MODE=microservices python scripts/run_ticket.py
```

---

## Validation

**Tested**:
- ✅ Both modes run successfully
- ✅ Same business logic behavior
- ✅ Performance benchmarks meet requirements
- ✅ Easy mode switching

**Metrics**:
- Monolith: P95 < 5ms latency
- Microservices: P95 < 25ms latency
- Both: 100% success rate under load

---

## References

- [DUAL_MODE_GUIDE.md](../guides/DUAL_MODE_GUIDE.md)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)

---

**Related ADRs**: ADR-004 (HTTP Connection Pooling)
