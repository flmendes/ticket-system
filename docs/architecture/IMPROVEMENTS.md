# Project Improvement Recommendations

## Executive Summary

This document provides comprehensive recommendations for improving the ticket-system microservices project across three key areas: **Performance**, **Folder Structure**, and **Standardization**.

---

## 1. Performance Improvements

### 1.1 HTTP Client Pooling (CRITICAL)

**Current Issue**: `ticket_service.py:22-33` creates a new `AsyncClient` for every request, leading to:
- Unnecessary TCP connection overhead
- Socket exhaustion under high load
- Increased latency

**Recommendation**: Use a shared client with connection pooling

```python
# ticket_service.py
from contextlib import asynccontextmanager

# Shared HTTP client
http_client: httpx.AsyncClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global http_client
    http_client = httpx.AsyncClient(
        timeout=5.0,
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100
        )
    )
    yield
    # Shutdown
    await http_client.aclose()

app = FastAPI(title="Ticket Sale Service", lifespan=lifespan)

async def reserve_vacancy(qty: int) -> dict:
    resp = await http_client.post(
        f"{VACANCY_URL}/reserve",
        json={"qty": qty}
    )
    # ... rest of code
```

**Expected Impact**: 30-50% reduction in request latency

### 1.2 Response Caching

**Current Issue**: Every `/available` request hits the Stock lock, even when inventory doesn't change frequently

**Recommendation**: Add short-lived caching (1-2 seconds) for availability queries

```python
from datetime import datetime, timedelta

class Stock:
    def __init__(self, total: int):
        self.total = total
        self.lock = asyncio.Lock()
        self._cached_total: int | None = None
        self._cache_expiry: datetime | None = None

    async def current(self, use_cache: bool = True) -> int:
        if use_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
            return self._cached_total

        async with self.lock:
            self._cached_total = self.total
            self._cache_expiry = datetime.now() + timedelta(seconds=1)
            return self.total
```

**Expected Impact**: Reduces lock contention during high-volume reads

### 1.3 Configuration Optimization

**Current Issue**: Hard-coded timeout (5s) may be too generous for localhost communication

**Recommendation**: Make timeouts configurable, use shorter defaults for internal services

```python
VACANCY_TIMEOUT = float(os.getenv("VACANCY_TIMEOUT", "2.0"))  # 2s for internal services
```

### 1.4 Add Response Compression

**Recommendation**: Enable gzip compression for responses

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

---

## 2. Folder Structure Improvements

### 2.1 Current Structure Issues

```
ticket-system/
├── src/
│   ├── ticket_service/
│   │   ├── __init__.py
│   │   └── ticket_service.py         # ❌ Redundant naming
│   └── vacancy_service/
│       ├── __init__.py
│       └── vacancy_service.py        # ❌ Redundant naming
├── run_ticket.py                     # ❌ Inconsistent location
├── run_vacancy.py                    # ❌ Inconsistent location
├── main.py                           # ❌ Unused file
└── pyproject.toml
```

**Problems**:
- Module import becomes `ticket_service.ticket_service` (redundant)
- Runner scripts outside `src/` break package conventions
- No separation of concerns (models, routes, config mixed)
- No tests directory
- No shared utilities

### 2.2 Recommended Structure

```
ticket-system/
├── src/
│   ├── common/                       # ✅ Shared code
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration management
│   │   ├── models.py                 # Shared Pydantic models
│   │   ├── logging.py                # Logging setup
│   │   └── middleware.py             # Shared middleware
│   │
│   ├── ticket/                       # ✅ Cleaner name
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app setup
│   │   ├── config.py                 # Service-specific config
│   │   ├── models.py                 # Request/Response models
│   │   ├── routes.py                 # API endpoints
│   │   ├── services.py               # Business logic
│   │   └── dependencies.py           # Dependency injection
│   │
│   ├── vacancy/                      # ✅ Cleaner name
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app setup
│   │   ├── config.py                 # Service-specific config
│   │   ├── models.py                 # Request/Response models
│   │   ├── routes.py                 # API endpoints
│   │   ├── services.py               # Stock management
│   │   └── dependencies.py           # Dependency injection
│   │
│   └── scripts/                      # ✅ Runner scripts
│       ├── run_ticket.py
│       └── run_vacancy.py
│
├── tests/                            # ✅ Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_ticket/
│   │   ├── __init__.py
│   │   ├── test_routes.py
│   │   └── test_services.py
│   └── test_vacancy/
│       ├── __init__.py
│       ├── test_routes.py
│       └── test_services.py
│
├── pyproject.toml
├── docker-compose.yml
├── .env.example                      # ✅ Environment template
└── README.md
```

### 2.3 Benefits

- **Clear separation of concerns**: Routes, models, business logic separated
- **Better imports**: `from ticket.routes import router` vs `from ticket_service.ticket_service import app`
- **Testability**: Easier to mock and test individual components
- **Scalability**: Easy to add new features (auth, monitoring, etc.)
- **Shared code**: Common utilities in one place

---

## 3. Standardization Improvements

### 3.1 Code Quality & Standards

#### Add Type Hints Everywhere
```python
# Current - missing type hints
async def reserve_vacancy(qty: int) -> dict:  # ❌ dict is vague

# Recommended
async def reserve_vacancy(qty: int) -> ReserveResponse:  # ✅ Explicit return type
```

#### Fix Import Inconsistencies
```python
# Current - mixed styles
from fastapi.applications import FastAPI  # ❌ Unnecessary specificity
from pydantic.main import BaseModel       # ❌

# Recommended
from fastapi import FastAPI               # ✅
from pydantic import BaseModel            # ✅
```

#### Remove Unused Imports
```python
# ticket_service.py:4
import json  # ❌ Not used anywhere
```

### 3.2 Configuration Management

Create a centralized config module:

```python
# src/common/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Service info
    service_name: str = "ticket-system"
    environment: str = "development"

    # Server config
    host: str = "0.0.0.0"
    port: int = 8002
    reload: bool = True

    # External services
    vacancy_url: str = "http://localhost:8001"
    vacancy_timeout: float = 2.0

    # Performance
    http_max_connections: int = 100
    http_keepalive_connections: int = 20

    # Stock config
    initial_stock: int = 1000
    cache_ttl_seconds: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 3.3 Logging Standardization

```python
# src/common/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

Usage:
```python
logger = setup_logging("ticket-service")
logger.info("Processing purchase", extra={"qty": req.qty, "user_id": 123})
```

### 3.4 Error Response Standardization

```python
# src/common/models.py
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str

class SuccessResponse(BaseModel):
    success: bool
    message: str | None = None
```

### 3.5 Health Check Endpoints

```python
# Add to both services
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ticket-service"}

@app.get("/ready")
async def readiness_check():
    # Check dependencies
    try:
        # For ticket service: ping vacancy service
        resp = await http_client.get(f"{VACANCY_URL}/health", timeout=1.0)
        return {"status": "ready", "dependencies": {"vacancy": "up"}}
    except:
        raise HTTPException(status_code=503, detail="Not ready")
```

### 3.6 API Versioning

```python
# src/ticket/routes.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["tickets"])

@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_ticket(req: PurchaseRequest):
    # ... implementation
```

### 3.7 OpenAPI Documentation Enhancement

```python
app = FastAPI(
    title="Ticket Sale Service",
    description="Microservice for ticket purchases with inventory management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.post(
    "/purchase",
    response_model=PurchaseResponse,
    summary="Purchase tickets",
    description="Attempt to purchase a specified quantity of tickets",
    responses={
        200: {"description": "Purchase successful or failed"},
        400: {"description": "Invalid request"},
        500: {"description": "Service unavailable"}
    }
)
async def purchase_ticket(req: PurchaseRequest):
    """
    Purchase tickets by reserving inventory from the vacancy service.

    - **qty**: Number of tickets to purchase (must be > 0)

    Returns purchase status and remaining inventory.
    """
    # ... implementation
```

### 3.8 Add Testing Infrastructure

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from ticket.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_vacancy_service(monkeypatch):
    # Mock httpx client
    pass

# tests/test_ticket/test_routes.py
def test_purchase_success(client, mock_vacancy_service):
    response = client.post("/purchase", json={"qty": 5})
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### 3.9 Environment Configuration

Create `.env.example`:
```bash
# Service Configuration
SERVICE_NAME=ticket-service
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8002
RELOAD=true

# External Services
VACANCY_URL=http://localhost:8001
VACANCY_TIMEOUT=2.0

# Performance
HTTP_MAX_CONNECTIONS=100
HTTP_KEEPALIVE_CONNECTIONS=20

# Stock
INITIAL_STOCK=1000
CACHE_TTL_SECONDS=1
```

### 3.10 Add CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure per environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 4. Additional Recommendations

### 4.1 Monitoring & Observability

Add Prometheus metrics:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 4.2 Graceful Shutdown

```python
import signal

async def shutdown_handler():
    logger.info("Shutting down...")
    await http_client.aclose()
    # Close other resources

# Register signal handlers
signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(shutdown_handler()))
```

### 4.3 Request ID Tracing

```python
# src/common/middleware.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### 4.4 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/purchase")
@limiter.limit("10/minute")
async def purchase_ticket(request: Request, req: PurchaseRequest):
    # ... implementation
```

---

## 5. Priority Implementation Order

### Phase 1 (Quick Wins - 1-2 days)
1. Fix HTTP client pooling (CRITICAL for performance)
2. Add logging
3. Fix typo: "sucessful" → "successful"
4. Remove unused imports/files
5. Add health check endpoints

### Phase 2 (Standardization - 3-5 days)
1. Implement configuration management
2. Standardize error responses
3. Add API versioning
4. Improve OpenAPI documentation
5. Add basic tests

### Phase 3 (Restructuring - 1 week)
1. Reorganize folder structure
2. Separate concerns (routes, models, services)
3. Create shared common module
4. Update Docker files for new structure

### Phase 4 (Advanced - Ongoing)
1. Add monitoring/metrics
2. Implement caching
3. Add rate limiting
4. Request tracing
5. Performance optimization

---

## 6. Estimated Impact

| Improvement | Performance Gain | Development Velocity | Maintainability |
|-------------|------------------|---------------------|-----------------|
| HTTP Client Pooling | 🔥🔥🔥 (30-50%) | - | ⭐ |
| Response Caching | 🔥🔥 (20-30%) | - | ⭐⭐ |
| Folder Restructure | - | ⭐⭐⭐ | ⭐⭐⭐ |
| Config Management | - | ⭐⭐⭐ | ⭐⭐⭐ |
| Logging | 🔥 (debugging) | ⭐⭐⭐ | ⭐⭐ |
| Testing | - | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 7. Bugs to Fix

1. **Typo**: `ticket_service.py:46` - "sucessful" → "successful"
2. **Unused import**: `ticket_service.py:4` - Remove `import json`
3. **Unused file**: `main.py` - Delete or repurpose
4. **Inconsistent imports**: Use standard FastAPI/Pydantic imports
