# Ticket System - Dual Mode Architecture 🚀

Sistema de reserva de ingressos construído com FastAPI, suportando **dois modos de deployment**: monolito (alta performance) e microserviços (escalabilidade). Inclui connection pooling, caching, gerenciamento atômico de estoque e arquitetura limpa.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-green.svg)](https://fastapi.tiangolo.com/)
[![Performance](https://img.shields.io/badge/P95%20Latency-10.75ms-brightgreen.svg)](./PERFORMANCE_BASELINE.md)
[![Dual Mode](https://img.shields.io/badge/Deployment-Monolith%20%7C%20Microservices-blue.svg)](./DUAL_MODE_GUIDE.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Optimized-blue.svg)](./docs/DOCKER_OPTIMIZATION.md)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-green.svg)](./docs/KUBERNETES_DEPLOY_SUCCESS.md)

---

## 📑 Índice

- [Deployment Modes](#-deployment-modes)
- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Performance](#-performance)
- [Quick Start](#-quick-start)
- [Documentação](#-documentação)
- [Desenvolvimento](#-desenvolvimento)
- [Testes de Carga](#-testes-de-carga)
- [Docker Otimizado](#-docker-otimizado)
- [Kubernetes](#-kubernetes)

---

## 🎯 Deployment Modes

Este projeto suporta **dois modos de deployment**:

### 🚀 Monolith Mode (Recommended for Development)

```bash
python scripts/run_monolith.py
```

- ✅ **Um único processo** - Todos os serviços juntos
- ✅ **Chamadas diretas** - Zero overhead de rede
- ✅ **Latência mínima** - ~0.5-2ms (15x mais rápido)
- ✅ **Simplicidade** - Fácil de debugar e desenvolver
- ✅ **Porta única** - http://localhost:8000

**Quando usar**: Desenvolvimento local, pequena escala, máxima performance.

### �� Microservices Mode (Recommended for Production)

```bash
# Terminal 1
python scripts/run_vacancy.py

# Terminal 2
python scripts/run_ticket.py
```

- ✅ **Processos independentes** - Escalabilidade horizontal
- ✅ **Isolamento de falhas** - Um serviço não derruba outro
- ✅ **Escalabilidade** - Escale cada serviço independentemente
- ✅ **Portas separadas** - Vacancy (8001), Ticket (8002)

**Quando usar**: Produção, larga escala, múltiplos times.

📚 **Guia completo**: [DUAL_MODE_GUIDE.md](./docs/guides/DUAL_MODE_GUIDE.md)

---

## 🎨 Visão Geral

Sistema de microserviços para gerenciamento de vendas de ingressos com:

- ⚡ **Alta Performance**: P95 latency de 10.75ms
- 📈 **Escalável**: Suporta 100+ usuários simultâneos
- 🔒 **Thread-Safe**: Gerenciamento atômico de estoque
- 🎯 **Moderno**: FastAPI, asyncio, type hints completos
- 👁️ **Observável**: Health checks, logging estruturado
- �� **Documentado**: OpenAPI/Swagger automático
- 🐳 **Docker Ultra-otimizado**: Imagens 63.8% menores (77MB vs 213MB)
- ☸️ **Kubernetes Ready**: Deploy automático com HPAs

### Características Principais

- **Connection Pooling**: HTTP client compartilhado para melhor performance
- **Caching Inteligente**: Reduz contenção de lock em consultas
- **API Versioning**: Endpoints `/api/v1` para evolução controlada
- **Configuração Centralizada**: pydantic-settings com .env
- **Middleware Stack**: CORS, GZip, error handling
- **Arquitetura Limpa**: Separação em camadas (routes, services, dependencies)

---

## 🏗️ Arquitetura

### Microserviços

```
                                            
  Ticket Service         > Vacancy Service  
    (Port 8002)    HTTP      (Port 8001)    
                                            
                                    
                                    
        v                            v
  Purchase API              Stock Management
  (Orquestrador)              (Atômico)
```

### Fluxo de Requisição

```
Cliente → POST /api/v1/purchase (Ticket Service)
              ↓
        HTTP Client Pool
              ↓
        POST /api/v1/reserve (Vacancy Service)
              ↓
        Stock Lock (asyncio)
              ↓
        Reservation Success/Fail
              ↓
        Response to Client
```

### Estrutura do Projeto

```
ticket-system/
├── src/
│   ├── common/              # Shared utilities
│   │   ├── config.py       # Configuration (pydantic-settings)
│   │   ├── models.py       # Shared Pydantic models
│   │   ├── logging.py      # Logging setup
│   │   └── http_client.py  # HTTP client pooling
│   │
│   ├── vacancy/            # Vacancy microservice
│   │   ├── main.py         # FastAPI app
│   │   ├── routes.py       # API endpoints
│   │   ├── services.py     # Business logic (StockManager)
│   │   └── dependencies.py # DI container
│   │
│   └── ticket/             # Ticket microservice
│       ├── main.py         # FastAPI app
│       ├── routes.py       # API endpoints
│       ├── services.py     # Business logic (TicketService)
│       └── dependencies.py # DI container
│
├── scripts/
│   ├── run_vacancy.py      # Run vacancy service
│   ├── run_ticket.py       # Run ticket service
│   └── run_monolith.py     # Run monolith mode
│
├── k8s/                    # Kubernetes manifests
├── tests/load/             # Load testing scripts
├── docs/                   # Documentation
├── docker-compose.yml      # Docker orchestration
└── Dockerfile.{service}    # Optimized Docker images
```

---

## ⚡ Performance

### Resultados do Baseline v1.0.0

| Métrica | Valor | Status |
|---------|-------|--------|
| **P95 Latency** | 10.75ms | ✅ Excelente |
| **Avg Latency** | 4.61ms | ✅ Excelente |
| **Throughput** | 197.86 req/s | ✅ Ótimo |
| **HTTP Failures** | 0% | ✅ Perfeito |
| **Concorrência** | 100 VUs | ✅ Estável |

### Comparação com Arquitetura Anterior

- ⚡ **96% mais rápido** - P95 latency: 257ms → 10.75ms
- 🚀 **95% mais rápido** - Avg latency: 101ms → 4.61ms
- 📈 **19% maior throughput** - 166 → 197.86 req/s

📊 **Veja**: [PERFORMANCE_BASELINE.md](./docs/performance/PERFORMANCE_BASELINE.md) para análise completa

---

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11.5+
- [uv](https://github.com/astral-sh/uv) (gerenciador de pacotes)
- K6 (opcional, para testes de carga)
- Docker + Docker Compose (opcional)

### Instalação

```bash
# 1. Clonar repositório
git clone <repo-url>
cd ticket-system

# 2. Instalar dependências
uv sync

# 3. Configurar ambiente (opcional)
cp .env.example .env
# Edite .env conforme necessário
```

### Execução Local

#### Modo Monolito (Recomendado para desenvolvimento)

```bash
python scripts/run_monolith.py
```

#### Modo Microserviços

```bash
# Terminal 1 - Vacancy Service
python scripts/run_vacancy.py

# Terminal 2 - Ticket Service
python scripts/run_ticket.py
```

### Verificação

```bash
# Health checks
curl http://localhost:8001/api/v1/health  # Vacancy (microservices)
curl http://localhost:8002/api/v1/health  # Ticket (microservices)
curl http://localhost:8000/api/v1/health  # Monolith

# Check disponibilidade
curl http://localhost:8001/api/v1/available

# Comprar ticket
curl -X POST http://localhost:8002/api/v1/purchase \
  -H "Content-Type: application/json" \
  -d '{"qty": 1}'
```

### Documentação da API

- **Monolith Mode**: http://localhost:8000/docs
- **Vacancy Service**: http://localhost:8001/docs
- **Ticket Service**: http://localhost:8002/docs

---

## 📚 Documentação

### Guias Principais

- 📝 **[CLAUDE.md](./CLAUDE.md)** - Guia completo para desenvolvimento
- 🏗️ **[ARCHITECTURE_IMPROVEMENTS.md](./docs/architecture/ARCHITECTURE_IMPROVEMENTS.md)** - Arquitetura monolito + microserviços
- 💡 **[IMPROVEMENTS.md](./docs/architecture/IMPROVEMENTS.md)** - Melhorias recomendadas
- ✅ **[IMPROVEMENTS_APPLIED.md](./docs/architecture/IMPROVEMENTS_APPLIED.md)** - Melhorias implementadas
- 🔄 **[MIGRATION_SUMMARY.md](./docs/architecture/MIGRATION_SUMMARY.md)** - Resumo da migração

### Performance

- ⚡ **[PERFORMANCE_BASELINE.md](./docs/performance/PERFORMANCE_BASELINE.md)** - Análise detalhada
- 📖 **[PERFORMANCE_QUICK_REFERENCE.md](./docs/performance/PERFORMANCE_QUICK_REFERENCE.md)** - Referência rápida
- 📊 **[PERFORMANCE_TEST_SUMMARY.md](./docs/performance/PERFORMANCE_TEST_SUMMARY.md)** - Resumo executivo

### Docker & Kubernetes

- 🐳 **[DOCKER_OPTIMIZATION.md](./docs/DOCKER_OPTIMIZATION.md)** - Otimizações aplicadas
- ☸️ **[KUBERNETES_DEPLOY_SUCCESS.md](./docs/KUBERNETES_DEPLOY_SUCCESS.md)** - Deploy Kubernetes

---

## 🛠️ Desenvolvimento

### Adicionar Nova Dependência

```bash
# Dependência de produção
uv add <package-name>

# Dependência de desenvolvimento
uv add --dev <package-name>
```

### Adicionar Novo Endpoint

1. Definir modelos em `src/common/models.py`
2. Implementar lógica em `src/<service>/services.py`
3. Criar rota em `src/<service>/routes.py`
4. Testar via `/docs`

### Configuração

Edite `.env` ou use variáveis de ambiente:

```bash
# Service
SERVICE_NAME=ticket-system
ENVIRONMENT=development

# Servers
VACANCY_PORT=8001
TICKET_PORT=8002

# Performance
HTTP_MAX_CONNECTIONS=100
HTTP_KEEPALIVE_CONNECTIONS=20

# Stock
INITIAL_STOCK=1000
CACHE_TTL_SECONDS=1

# Logging
LOG_LEVEL=INFO
JSON_LOGS=false
```

---

## 🧪 Testes de Carga

### Executar Teste Padrão

```bash
# Certifique-se que os serviços estão rodando
k6 run tests/load/ticket-system-k6.js
```

### Teste com Configuração Custom

```bash
# Mudar quantidade de tickets por compra
QTY=5 k6 run tests/load/ticket-system-k6.js

# Mudar URLs dos serviços
VU_BASE_URL=http://prod:8002 \
VU_VACANCY_URL=http://prod:8001 \
k6 run tests/load/ticket-system-k6.js
```

### Cenários do Teste

- **50 VUs**: Consultas de disponibilidade (`GET /api/v1/available`)
- **50 VUs**: Compras de tickets (`POST /api/v1/purchase`)
- **Duração**: 60 segundos
- **Total**: ~200 requisições/segundo

### Thresholds

✅ **PASS**: P95 < 500ms, purchase_success > 0%

---

## 🐳 Docker Otimizado

### Imagens Ultra-Otimizadas

- **Tecnologia**: Multi-stage builds com Distroless
- **Tamanho Original**: 213MB
- **Tamanho Atual**: 77.2MB
- **Redução**: 63.8% (135.8MB economizados)

### Docker Compose

```bash
# Build e start (imagens otimizadas por padrão)
docker compose up --build

# Detached mode
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Build Manual

```bash
# Build otimizado (padrão)
make build

# Build Alpine para debug
make build-alpine

# Script auxiliar
./build-optimized.sh
```

### Características das Imagens

- ✅ **Distroless**: Sem shell, máxima segurança
- ✅ **Multi-stage**: Build e runtime separados
- ✅ **Usuário não-root**: Segurança aprimorada
- ✅ **Python otimizado**: Configurações de performance

📖 **Documentação completa**: [DOCKER_OPTIMIZATION.md](./docs/DOCKER_OPTIMIZATION.md)

---

## ☸️ Kubernetes

### Deploy Rápido

```bash
# Deploy completo no Kind
make full-deploy
```

### Deploy Manual

```bash
# Aplicar manifestos
kubectl apply -f k8s/

# Verificar status
make status

# Testar aplicação
make test
```

### Recursos Incluídos

- ✅ **Deployments**: Ticket e Vacancy services
- ✅ **Services**: ClusterIP para comunicação interna
- ✅ **Ingress**: Acesso externo via nginx
- ✅ **HPAs**: Auto-scaling baseado em CPU/memória
- ✅ **ConfigMaps**: Configurações centralizadas

### Monitoramento

```bash
# Status dos HPAs
make hpa-status

# Logs dos serviços
make logs

# Métricas dos pods
kubectl top pods -n ticket-system
```

### Acesso

- **Aplicação**: http://ticket.127.0.0.1.nip.io/
- **API Docs**: http://ticket.127.0.0.1.nip.io/docs
- **Health**: http://ticket.127.0.0.1.nip.io/api/v1/health

📖 **Guia completo**: [KUBERNETES_DEPLOY_SUCCESS.md](./docs/KUBERNETES_DEPLOY_SUCCESS.md)

---

## 🔧 Troubleshooting

### Serviços não iniciam

```bash
# Verificar portas disponíveis
lsof -i :8001
lsof -i :8002

# Reinstalar dependências
uv sync --reinstall
```

### Ticket service não alcança vacancy service

```bash
# Verificar vacancy service
curl http://localhost:8001/api/v1/health

# Verificar configuração
echo $VACANCY_URL  # Deve ser http://localhost:8001
```

### Performance degradada

```bash
# Executar teste de carga
k6 run tests/load/ticket-system-k6.js

# Comparar com baseline
# P95 deve ser < 50ms
# Throughput deve ser > 180 req/s
```

### Problemas no Kubernetes

```bash
# Verificar pods
kubectl get pods -n ticket-system

# Logs detalhados
kubectl describe pod -n ticket-system <pod-name>

# HPAs
kubectl get hpa -n ticket-system
```

---

## 📋 Endpoints da API

### Vacancy Service (Port 8001)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/available` | Consultar disponibilidade |
| POST | `/api/v1/reserve` | Reservar tickets |
| GET | `/api/v1/health` | Health check |
| GET | `/` | Informações do serviço |
| GET | `/docs` | Documentação OpenAPI |

### Ticket Service (Port 8002)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/purchase` | Comprar tickets |
| GET | `/api/v1/health` | Health check |
| GET | `/ready` | Readiness check |
| GET | `/` | Informações do serviço |
| GET | `/docs` | Documentação OpenAPI |

### Monolith Mode (Port 8000)

Todos os endpoints acima disponíveis em uma única porta.

---

## 👥 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/amazing`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para a branch (`git push origin feature/amazing`)
5. Abra um Pull Request

### Guidelines

- Mantenha type hints em todo código
- Execute testes de carga após mudanças significativas
- Atualize documentação conforme necessário
- Siga a arquitetura em camadas existente

---

## 📄 License

Este projeto está sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

**Flavio Mendes**
- Email: flmendes@gmail.com

---

## 🙏 Agradecimentos

- FastAPI pela excelente framework
- K6 pela ferramenta de load testing
- uv pelo gerenciador de pacotes rápido
- Distroless pela imagens ultra-seguras

---

## 📊 Status do Projeto

- ✅ **Arquitetura**: Clean Architecture implementada
- ✅ **Performance**: Baseline estabelecido (P95: 10.75ms)
- ✅ **Documentação**: Completa e atualizada
- ✅ **Docker**: Imagens ultra-otimizadas (77MB)
- ✅ **Kubernetes**: Deploy automático com HPAs
- ✅ **Testes de Carga**: K6 configurado e validado
- 🔄 **Testes Unitários**: A implementar
- 🔄 **CI/CD**: A implementar
- 🔄 **Monitoring**: A implementar

---

**Última Atualização**: 2025-11-02  
**Versão**: 1.0.0  
**Docker**: Ultra-otimizado (63.8% menor)  
**Kubernetes**: Production Ready ☸️
