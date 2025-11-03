# Dual Mode Guide - Monolith + Microservices

## 🎯 Overview

O sistema agora suporta **dois modos de deployment**:

1. **Monolithic Mode** 🚀 - Todos os serviços em um único processo com chamadas diretas
2. **Microservices Mode** 🔗 - Serviços independentes comunicando via HTTP

A mesma codebase funciona em ambos os modos, sem modificações!

---

## ⚡ Performance Comparison

| Aspect | Monolith | Microservices |
|--------|----------|---------------|
| **Latency (P95)** | ~0.5-2ms | ~10-15ms |
| **Network Overhead** | Zero | HTTP per request |
| **Memory** | ~50MB | ~100MB (2 processes) |
| **Deployment** | 1 process | 2+ processes |
| **Scalability** | Vertical only | Horizontal |
| **Complexity** | Low | Higher |

### When to Use Each Mode

**Monolith** 👍
- Development local
- Pequena escala (< 1000 req/s)
- Máxima performance necessária
- Simplicidade operacional

**Microservices** 👍
- Produção em larga escala
- Necessidade de escalar serviços independentemente
- Múltiplos times trabalhando
- Isolamento de falhas crítico

---

## 🚀 How to Run

### Modo 1: Monolith (Recommended for Development)

```bash
# Executar tudo em um único processo
python scripts/run_monolith.py
```

**Acesso**:
- Todos os endpoints: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Vacancy endpoints: http://localhost:8000/api/v1/available
- Ticket endpoints: http://localhost:8000/api/v1/purchase

**Características**:
- ✅ Um único processo
- ✅ Chamadas diretas (sem HTTP)
- ✅ Latência mínima (~1-2ms)
- ✅ Simplicidade máxima
- ✅ Fácil debug

### Modo 2: Microservices (Current Behavior)

```bash
# Terminal 1 - Vacancy Service
python scripts/run_vacancy.py

# Terminal 2 - Ticket Service
python scripts/run_ticket.py
```

**Acesso**:
- Vacancy Service: http://localhost:8001
  - API Docs: http://localhost:8001/docs
- Ticket Service: http://localhost:8002
  - API Docs: http://localhost:8002/docs

**Características**:
- ✅ Processos independentes
- ✅ Escalabilidade horizontal
- ✅ Isolamento de falhas
- ⚠️ Overhead de rede HTTP

---

## 🧪 Testing

### Test Monolith Mode

```bash
# 1. Start monolith
python scripts/run_monolith.py

# 2. Test (in another terminal)
# Check availability
curl http://localhost:8000/api/v1/available

# Purchase ticket
curl -X POST http://localhost:8000/api/v1/purchase \
  -H "Content-Type: application/json" \
  -d '{"qty": 1}'

# Check mode
curl http://localhost:8000/ | jq .mode
# Should return: "monolith"
```

### Test Microservices Mode

```bash
# 1. Start services (2 terminals)
python scripts/run_vacancy.py  # Terminal 1
python scripts/run_ticket.py   # Terminal 2

# 2. Test (in another terminal)
# Check availability
curl http://localhost:8001/api/v1/available

# Purchase ticket
curl -X POST http://localhost:8002/api/v1/purchase \
  -H "Content-Type: application/json" \
  -d '{"qty": 1}'

# Check mode
curl http://localhost:8002/ | jq .deployment_mode
# Should return: "microservices"
```

---

## 🏗️ Architecture

### How It Works

A arquitetura usa **Dependency Injection** e **Strategy Pattern** para selecionar automaticamente entre local e remote:

```python
# domain/interfaces.py
class VacancyClient(Protocol):
    """Interface - both implementations satisfy this contract"""
    async def reserve(self, request: ReserveRequest) -> ReserveResponse:
        ...

# ticket/clients/local.py
class LocalVacancyClient:
    """Direct function calls - no HTTP"""
    async def reserve(self, request):
        return await self._service.reserve(request.qty)  # Direct!

# ticket/clients/remote.py
class RemoteVacancyClient:
    """HTTP calls with connection pooling"""
    async def reserve(self, request):
        response = await self.http_client.post(...)  # HTTP
        return ReserveResponse(**response.json())

# ticket/clients/__init__.py
def create_vacancy_client() -> VacancyClient:
    """Factory - chooses based on DEPLOYMENT_MODE"""
    if settings.deployment_mode == DeploymentMode.MONOLITH:
        return LocalVacancyClient()  # Zero network overhead!
    else:
        return RemoteVacancyClient()  # HTTP with pooling
```

### Key Components

**Domain Layer** (`src/domain/`)
- `interfaces.py` - Protocol definitions (VacancyClient)
- `exceptions.py` - Business exceptions

**Vacancy Service** (`src/vacancy/`)
- `services.py` - StockManager, VacancyService (business logic)
- `routes.py` - FastAPI endpoints
- `main.py` - FastAPI app
- `dependencies.py` - DI container

**Ticket Service** (`src/ticket/`)
- `services.py` - TicketService (uses VacancyClient interface)
- `clients/local.py` - Direct calls implementation
- `clients/remote.py` - HTTP calls implementation
- `clients/__init__.py` - Factory
- `routes.py` - FastAPI endpoints
- `main.py` - FastAPI app (conditional HTTP client init)
- `dependencies.py` - DI container

**Applications** (`src/apps/`)
- `monolith.py` - Combined app for monolithic mode

**Runners** (`scripts/`)
- `run_monolith.py` - Run in monolith mode
- `run_vacancy.py` - Run vacancy microservice
- `run_ticket.py` - Run ticket microservice

---

## ⚙️ Configuration

### Via Environment Variable

```bash
# Monolith mode
export DEPLOYMENT_MODE=monolith
python scripts/run_monolith.py

# Microservices mode (default)
export DEPLOYMENT_MODE=microservices
python scripts/run_vacancy.py  # Terminal 1
python scripts/run_ticket.py   # Terminal 2
```

### Via .env File

```bash
# .env
DEPLOYMENT_MODE=monolith  # or microservices

# Monolith specific
MONOLITH_PORT=8000

# Microservices specific
TICKET_PORT=8002
VACANCY_PORT=8001
VACANCY_URL=http://localhost:8001
```

### Via Code (for testing)

```python
import os
os.environ["DEPLOYMENT_MODE"] = "monolith"

from apps.monolith import app
# App will use local client automatically
```

---

## 📊 Performance Testing

### Monolith Mode

```bash
# Start
python scripts/run_monolith.py

# Run load test (adjust script)
cat > ticket-system-k6-monolith.js << 'EOF'
import http from "k6/http";
const BASE_URL = "http://localhost:8000";  // Single endpoint
const VACANCY_URL = "http://localhost:8000";

// ... rest of k6 script
EOF

k6 run ticket-system-k6-monolith.js
```

**Expected Results**:
- P95 Latency: ~0.5-2ms (much faster!)
- Throughput: ~500-1000 req/s
- No HTTP failures

### Microservices Mode

```bash
# Start
python scripts/run_vacancy.py  # Terminal 1
python scripts/run_ticket.py   # Terminal 2

# Run existing load test
k6 run ticket-system-k6.js
```

**Expected Results** (from baseline):
- P95 Latency: ~10-15ms
- Throughput: ~200 req/s
- No HTTP failures

---

## 🐳 Docker

### Monolith Docker

```dockerfile
# Dockerfile.monolith
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY scripts/ ./scripts/

ENV DEPLOYMENT_MODE=monolith

EXPOSE 8000

CMD ["uv", "run", "python", "scripts/run_monolith.py"]
```

### Docker Compose - Monolith

```yaml
# docker-compose.monolith.yml
version: '3.8'

services:
  monolith:
    build:
      context: .
      dockerfile: Dockerfile.monolith
    container_name: ticket-system-monolith
    ports:
      - "8000:8000"
    environment:
      - DEPLOYMENT_MODE=monolith
      - INITIAL_STOCK=10000
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

**Run**:
```bash
docker-compose -f docker-compose.monolith.yml up --build
```

### Docker Compose - Microservices

Already exists: `docker-compose.yml`

```bash
docker-compose up --build
```

---

## 🔀 Migration Path

### From Microservices to Monolith

1. Stop microservices
2. Start monolith:
   ```bash
   DEPLOYMENT_MODE=monolith python scripts/run_monolith.py
   ```
3. Update clients to use `http://localhost:8000`

### From Monolith to Microservices

1. Stop monolith
2. Start microservices:
   ```bash
   python scripts/run_vacancy.py  # Terminal 1
   python scripts/run_ticket.py   # Terminal 2
   ```
3. Update clients:
   - Vacancy: `http://localhost:8001`
   - Ticket: `http://localhost:8002`

---

## 🎓 Benefits

### Monolith Benefits

1. **Performance**: Direct calls vs HTTP (10-15x faster)
2. **Simplicity**: One process to manage
3. **Development**: Easier to debug and develop
4. **Cost**: Lower resource usage
5. **Latency**: Sub-millisecond inter-service calls

### Microservices Benefits

1. **Scalability**: Scale services independently
2. **Isolation**: Failures don't cascade
3. **Technology**: Different tech stacks possible
4. **Teams**: Different teams own different services
5. **Deployment**: Deploy services independently

---

## 🧪 Example Usage

### Python Code

```python
# Works in both modes - no code changes needed!

import httpx

# Monolith
response = httpx.post(
    "http://localhost:8000/api/v1/purchase",
    json={"qty": 5}
)

# Microservices
response = httpx.post(
    "http://localhost:8002/api/v1/purchase",
    json={"qty": 5}
)

# Response is identical
print(response.json())
# {"success": true, "remaining": 995, "message": "Purchase successful!"}
```

### JavaScript/Node.js

```javascript
// Monolith
const response = await fetch('http://localhost:8000/api/v1/purchase', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({qty: 5})
});

// Microservices
const response = await fetch('http://localhost:8002/api/v1/purchase', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({qty: 5})
});

const data = await response.json();
console.log(data);
// {success: true, remaining: 995, message: "Purchase successful!"}
```

---

## 📋 Checklist

### Starting in Monolith Mode

- [ ] Set `DEPLOYMENT_MODE=monolith` (or in .env)
- [ ] Run `python scripts/run_monolith.py`
- [ ] Verify at http://localhost:8000
- [ ] Check `/` shows `"mode": "monolith"`
- [ ] Test purchase: should be very fast (<2ms)

### Starting in Microservices Mode

- [ ] Set `DEPLOYMENT_MODE=microservices` (default)
- [ ] Run `python scripts/run_vacancy.py`
- [ ] Run `python scripts/run_ticket.py`
- [ ] Verify vacancy at http://localhost:8001
- [ ] Verify ticket at http://localhost:8002
- [ ] Check `/` shows `"deployment_mode": "microservices"`
- [ ] Test purchase: should work (~10-15ms)

---

## 🎯 Summary

| Feature | Monolith | Microservices |
|---------|----------|---------------|
| **Command** | `python scripts/run_monolith.py` | `python scripts/run_vacancy.py` + `run_ticket.py` |
| **Ports** | 8000 | 8001 + 8002 |
| **Performance** | 🚀🚀🚀 Fastest | ⚡ Fast |
| **Complexity** | ✅ Simple | ⚠️ More complex |
| **Best For** | Dev, small scale | Production, large scale |
| **Inter-service** | Direct calls | HTTP |
| **Latency** | <2ms | ~10-15ms |

---

**Escolha o modo certo para sua necessidade:**
- 🏃 **Desenvolvimento rápido**: Monolith
- 🚀 **Performance máxima**: Monolith
- 📈 **Escalabilidade**: Microservices
- 🔒 **Isolamento**: Microservices

**A melhor parte**: Você pode mudar entre os modos facilmente!

---

**Versão**: 1.0.0
**Última atualização**: 2025-11-02
