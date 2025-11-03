# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **dual-mode ticket reservation system** built with FastAPI and managed with `uv`. The system can run as either a **monolith** (all services in one process with direct function calls) or as **microservices** (separate processes with HTTP communication), using the same codebase. The architecture demonstrates proper separation of concerns, dependency injection, and clean architecture principles.

### Deployment Modes

The system supports two deployment modes controlled by the `DEPLOYMENT_MODE` environment variable:

1. **Monolith Mode** (`DEPLOYMENT_MODE=monolith`)
   - All services run in a single process
   - Inter-service communication via direct function calls (zero network overhead)
   - Maximum performance: ~0.5-2ms latency
   - Best for: Development, small scale, performance-critical scenarios
   - Run with: `python scripts/run_monolith.py`
   - Port: 8000

2. **Microservices Mode** (`DEPLOYMENT_MODE=microservices`, default)
   - Services run as independent processes
   - Inter-service communication via HTTP with connection pooling
   - Horizontal scalability and fault isolation
   - Best for: Production, large scale, multiple teams
   - Run with: `python scripts/run_vacancy.py` + `python scripts/run_ticket.py`
   - Ports: Vacancy (8001), Ticket (8002)

**See [DUAL_MODE_GUIDE.md](./DUAL_MODE_GUIDE.md) for comprehensive dual-mode documentation.**

## Architecture

### Layered Architecture

The system uses a clean, layered architecture with dependency inversion:

```
┌─────────────────────────────────────┐
│     API Layer (routes.py)           │  ← FastAPI HTTP endpoints
├─────────────────────────────────────┤
│   Service Layer (services.py)       │  ← Business logic
├─────────────────────────────────────┤
│   Domain Layer (domain/)            │  ← Interfaces (Protocols) + Exceptions
├─────────────────────────────────────┤
│   Infrastructure (clients/)         │  ← LocalVacancyClient vs RemoteVacancyClient
├─────────────────────────────────────┤
│   Common Layer (common/)            │  ← Shared models, config, utilities
└─────────────────────────────────────┘
```

The **domain layer** defines interfaces using Python Protocols, allowing the service layer to depend on abstractions rather than concrete implementations. This enables the dual-mode architecture where the same business logic works with both local (direct call) and remote (HTTP) client implementations.

### Services

The system consists of two bounded contexts (services):

1. **Vacancy Service**: `src/vacancy/`
   - Manages available ticket inventory (configurable, default: 1000 tickets)
   - Thread-safe stock management using asyncio.Lock
   - Caching layer to reduce lock contention (configurable TTL)
   - Exposes `/api/v1/available` (GET) and `/api/v1/reserve` (POST) endpoints
   - All stock operations are atomic to prevent race conditions
   - **In microservices mode**: Runs on port 8001 as independent process
   - **In monolith mode**: Imported directly by the monolith app

2. **Ticket Service**: `src/ticket/`
   - Public-facing ticket purchase API
   - Communicates with Vacancy Service through the `VacancyClient` interface
   - Exposes `/api/v1/purchase` (POST) endpoint
   - Handles coordination and error propagation between services
   - **In microservices mode**: Runs on port 8002, uses `RemoteVacancyClient` (HTTP with connection pooling)
   - **In monolith mode**: Uses `LocalVacancyClient` (direct function calls, zero overhead)

### Service Communication Flow

**Microservices Mode** (HTTP):
```
Client → Ticket Service (/purchase) → [HTTP] → Vacancy Service (/reserve) → Stock
```

**Monolith Mode** (Direct Calls):
```
Client → Monolith App (/purchase) → [Direct Call] → VacancyService.reserve() → Stock
```

The Ticket Service depends on the `VacancyClient` Protocol interface (src/domain/interfaces.py:10). A factory function (src/ticket/clients/__init__.py:8) selects the appropriate implementation based on `DEPLOYMENT_MODE`.

## Project Structure

```
src/
├── domain/                    # Domain layer (business interfaces)
│   ├── __init__.py
│   ├── interfaces.py         # VacancyClient Protocol interface
│   └── exceptions.py         # Business exceptions (domain-agnostic)
│
├── common/                    # Shared utilities and infrastructure
│   ├── config.py             # Centralized configuration (pydantic-settings)
│   ├── models.py             # Shared Pydantic models
│   ├── logging.py            # Logging setup
│   └── http_client.py        # Shared HTTP client with connection pooling
│
├── vacancy/                   # Vacancy bounded context
│   ├── main.py               # FastAPI app setup
│   ├── routes.py             # API endpoints (v1)
│   ├── services.py           # Business logic (StockManager, VacancyService)
│   └── dependencies.py       # Dependency injection (singleton management)
│
├── ticket/                    # Ticket bounded context
│   ├── main.py               # FastAPI app setup (conditional HTTP client init)
│   ├── routes.py             # API endpoints (v1)
│   ├── services.py           # Business logic (TicketService - uses VacancyClient interface)
│   ├── dependencies.py       # Dependency injection (singleton management)
│   └── clients/              # Vacancy client implementations
│       ├── __init__.py       # Factory: create_vacancy_client()
│       ├── local.py          # LocalVacancyClient (direct calls for monolith)
│       └── remote.py         # RemoteVacancyClient (HTTP for microservices)
│
└── apps/                      # Application entry points
    ├── __init__.py
    └── monolith.py           # Combined FastAPI app for monolith mode

scripts/
├── run_monolith.py           # Run in monolith mode (port 8000)
├── run_vacancy.py            # Run vacancy service (microservices mode, port 8001)
└── run_ticket.py             # Run ticket service (microservices mode, port 8002)
```

## Development Commands

### First Time Setup

```bash
# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
```

### Running Services Locally

**Option 1: Monolith Mode** (Recommended for Development)

```bash
# Single process with direct calls
python scripts/run_monolith.py
```

Access:
- All endpoints: http://localhost:8000
- API docs: http://localhost:8000/docs
- Vacancy endpoints: http://localhost:8000/api/v1/available
- Ticket endpoints: http://localhost:8000/api/v1/purchase

**Option 2: Microservices Mode**

Start both services in separate terminals:

```bash
# Terminal 1 - Vacancy Service (port 8001)
python scripts/run_vacancy.py

# Terminal 2 - Ticket Service (port 8002)
python scripts/run_ticket.py
```

Access API documentation:
- Vacancy Service: http://localhost:8001/docs
- Ticket Service: http://localhost:8002/docs

Both modes run with auto-reload enabled for development.

### Running with Docker

Use Docker Compose to run both services in containers:

```bash
# Build and start both services
docker-compose up --build

# Start in detached mode
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild a specific service
docker-compose build ticket-service
docker-compose build vacancy-service
```

The Docker setup includes:
- Health checks for both services
- Automatic dependency management (ticket-service waits for vacancy-service)
- Bridge networking for inter-service communication
- Environment variable configuration

### Package Management

This project uses `uv` for dependency management:

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Update dependencies
uv lock --upgrade
```

### Load Testing

The project includes K6 load tests in `ticket‑system‑k6.js`:

```bash
# Run load tests (requires K6 installed)
k6 run ticket‑system‑k6.js

# With custom parameters
QTY=5 k6 run ticket‑system‑k6.js
```

The K6 tests run two scenarios concurrently:
- Availability checks: 50 VUs querying `/available`
- Purchase requests: 50 VUs attempting ticket purchases

## Key Implementation Details

### Dual-Mode Architecture (CRITICAL)

The system uses **Protocol-based interfaces** and **factory pattern** to support both deployment modes:

**Domain Layer** (`src/domain/interfaces.py:10`):
```python
@runtime_checkable
class VacancyClient(Protocol):
    """Interface that both Local and Remote clients implement"""
    async def reserve(self, request: ReserveRequest) -> ReserveResponse: ...
    async def get_available(self) -> AvailableResponse: ...
```

**Client Implementations**:
- `LocalVacancyClient` (src/ticket/clients/local.py:10): Direct function calls to VacancyService
- `RemoteVacancyClient` (src/ticket/clients/remote.py:15): HTTP calls with connection pooling

**Factory Selection** (src/ticket/clients/__init__.py:8):
```python
def create_vacancy_client() -> VacancyClient:
    if settings.deployment_mode == DeploymentMode.MONOLITH:
        return LocalVacancyClient()  # Zero network overhead
    else:
        return RemoteVacancyClient()  # HTTP with pooling
```

The `TicketService` depends only on the `VacancyClient` interface, not concrete implementations. This is **Dependency Inversion Principle** in action.

### Separation of Concerns

Each service follows a clear separation:
- **routes.py**: HTTP layer, request/response handling
- **services.py**: Business logic, transport-agnostic (depends on interfaces)
- **dependencies.py**: Dependency injection, singleton management
- **main.py**: Application setup, middleware configuration
- **clients/**: Infrastructure implementations (HTTP vs direct calls)

### HTTP Client Pooling (CRITICAL for Performance)

The ticket service uses a shared HTTP client with connection pooling (src/common/http_client.py:15):
```python
_http_client = httpx.AsyncClient(
    timeout=settings.vacancy_timeout,
    limits=httpx.Limits(
        max_keepalive_connections=settings.http_keepalive_connections,
        max_connections=settings.http_max_connections,
    ),
)
```

This prevents creating a new client for every request, providing:
- 30-50% reduction in latency
- Prevention of socket exhaustion under load
- Better resource utilization

### Concurrency Safety

The Vacancy Service uses `asyncio.Lock` to ensure thread-safe stock operations (src/vacancy/services.py:32):
```python
async with self.lock:
    if self.total >= qty:
        self.total -= qty
        return True, self.total
```

All stock reads and writes must acquire this lock to prevent race conditions during high-concurrency scenarios.

### Caching for Performance

The StockManager implements optional caching for read operations (src/vacancy/services.py:45):
- Reduces lock contention for frequent availability checks
- Configurable TTL (default: 1 second)
- Automatically invalidated on writes

### Error Handling

- Both services validate that quantity is > 0
- Ticket Service propagates HTTP errors from Vacancy Service with appropriate status codes
- Configurable timeout for inter-service communication (default: 2 seconds)
- Standardized error responses across services

### Health Checks

Both services expose health check endpoints:
- `/health`: Basic health check (returns immediately)
- `/ready`: Readiness check (verifies dependencies for ticket service)

Used by Docker, Kubernetes, and load balancers.

### API Versioning

All endpoints use `/api/v1` prefix for versioning:
- Enables backward compatibility
- Allows gradual API evolution
- Clear API lifecycle management

### Configuration Management

Centralized configuration using pydantic-settings (src/common/config.py):
- Environment variable support
- Type validation
- Default values
- .env file support

All configuration is cached for performance.

### Logging

Standardized logging across services:
- Configurable log level (INFO, DEBUG, WARNING, ERROR)
- JSON format option for production
- Structured logging with context
- Service-specific logger names

### Middleware

Both services include:
- CORS middleware (configure allowed origins for production)
- GZip compression for responses > 1KB
- Automatic error handling

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Deployment Mode (CRITICAL)
# monolith: All services in one process with direct calls (fastest)
# microservices: Services run separately with HTTP communication
DEPLOYMENT_MODE=microservices

# Service Configuration
SERVICE_NAME=ticket-system
ENVIRONMENT=development

# Server
HOST=0.0.0.0
MONOLITH_PORT=8000        # Port for monolith mode
TICKET_PORT=8002          # Port for ticket service (microservices mode)
VACANCY_PORT=8001         # Port for vacancy service (microservices mode)
RELOAD=true

# External Services (for ticket service in microservices mode only)
VACANCY_URL=http://localhost:8001
VACANCY_TIMEOUT=2.0

# Performance (HTTP client used only in microservices mode)
HTTP_MAX_CONNECTIONS=100
HTTP_KEEPALIVE_CONNECTIONS=20

# Stock
INITIAL_STOCK=1000
CACHE_TTL_SECONDS=1

# Logging
LOG_LEVEL=INFO
JSON_LOGS=false
```

**Important**: The `DEPLOYMENT_MODE` setting controls the entire architecture:
- `monolith`: Uses `LocalVacancyClient`, no HTTP client initialization
- `microservices`: Uses `RemoteVacancyClient`, initializes HTTP connection pool

## Common Development Tasks

### Adding a New Endpoint

1. Define request/response models in `src/common/models.py`
2. Add business logic to service layer (`services.py`)
3. Create route handler in `routes.py`
4. Test endpoint via `/docs`

### Modifying Business Logic

1. Update service layer (`services.py`)
2. Ensure type hints are correct
3. Update error handling if needed
4. Test with existing endpoints

### Adding Configuration

1. Add field to `Settings` class in `src/common/config.py`
2. Add to `.env.example` with description
3. Use via `get_settings()` in your code

## Performance Characteristics

### Typical Metrics (Development)

- **Availability Query**: ~1-5ms (cached), ~10-20ms (uncached)
- **Purchase Request**: ~15-30ms (includes HTTP roundtrip)
- **Throughput**: ~5,000 req/s per service
- **Memory**: ~50MB per service

### Optimization Opportunities

1. HTTP client pooling (already implemented)
2. Response caching (implemented for availability)
3. Database connection pooling (when adding persistence)
4. Circuit breakers for fault tolerance
5. Rate limiting for abuse prevention

## Troubleshooting

### Services won't start

1. Check if ports 8001/8002 are available
2. Verify dependencies installed: `uv sync`
3. Check configuration in `.env`
4. Review logs for specific errors

### Ticket service can't reach vacancy service

1. Verify vacancy service is running: `curl http://localhost:8001/health`
2. Check `VACANCY_URL` configuration
3. Verify network connectivity (Docker network for containers)
4. Check firewall settings

### Performance issues

1. Monitor HTTP client pooling settings
2. Check cache TTL configuration
3. Review logs for slow queries
4. Use K6 load tests to identify bottlenecks
5. Monitor Docker resource limits

## Docker Notes

- Services communicate via bridge network `ticket-network`
- Vacancy service must be healthy before ticket service starts
- Health checks use Python's urllib (no external dependencies)
- Environment variables override .env file settings
- Logs available via `docker-compose logs -f`
