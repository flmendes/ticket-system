# Troubleshooting Guide

## OSError: [Errno 24] Too many open files

### Problema

Ao executar testes de carga com 200+ usuários simultâneos, você pode receber:

```
OSError: [Errno 24] Too many open files
```

Este é um limite do sistema operacional para o número de arquivos (file descriptors) que um processo pode abrir.

---

## Soluções (Escolha uma ou combine)

### Solução 1: Aumentar Limite do Sistema (macOS)

#### Temporário (válido até reiniciar terminal)

```bash
# Verificar limite atual
ulimit -n

# Aumentar para 10,000 (sessão atual)
ulimit -n 10000

# Verificar novo limite
ulimit -n
```

#### Permanente (macOS)

1. Criar arquivo de configuração:

```bash
sudo nano /Library/LaunchDaemons/limit.maxfiles.plist
```

2. Adicionar conteúdo:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>limit.maxfiles</string>
    <key>ProgramArguments</key>
    <array>
      <string>launchctl</string>
      <string>limit</string>
      <string>maxfiles</string>
      <string>65536</string>
      <string>200000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>ServiceIPC</key>
    <false/>
  </dict>
</plist>
```

3. Aplicar:

```bash
sudo chown root:wheel /Library/LaunchDaemons/limit.maxfiles.plist
sudo launchctl load -w /Library/LaunchDaemons/limit.maxfiles.plist
```

4. Reiniciar o Mac

---

### Solução 2: Configurar Uvicorn para Limitar Workers

Edite `scripts/run_vacancy.py` e `scripts/run_ticket.py`:

```python
#!/usr/bin/env python3
"""Run vacancy service."""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import uvicorn
from common.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "vacancy.main:app",
        host=settings.host,
        port=settings.vacancy_port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        # Limitar recursos
        workers=1,                    # Número de workers (evitar múltiplos processos)
        backlog=2048,                 # Fila de conexões pendentes
        limit_concurrency=500,        # Limite de requisições simultâneas
        timeout_keep_alive=5,         # Keep-alive timeout
    )
```

---

### Solução 3: Ajustar Configuração do HTTP Client

Edite `src/common/config.py`:

```python
class Settings(BaseSettings):
    # ... campos existentes ...

    # HTTP Client - Reduzir para menos file descriptors
    http_max_connections: int = 50        # Era 100
    http_keepalive_connections: int = 10  # Era 20
```

---

### Solução 4: Usar Gunicorn com Uvicorn Workers (Produção)

Para produção, use Gunicorn:

```bash
# Instalar
uv add gunicorn

# Executar
gunicorn vacancy.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001 \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100
```

---

### Solução 5: Ajustar Teste K6 (Ramp-up Gradual)

Em vez de 200 VUs instantâneos, use ramp-up:

Crie `ticket-system-k6-stress.js`:

```javascript
export let options = {
  stages: [
    { duration: '30s', target: 50 },   // Ramp up para 50
    { duration: '30s', target: 100 },  // Ramp up para 100
    { duration: '30s', target: 200 },  // Ramp up para 200
    { duration: '1m', target: 200 },   // Manter 200
    { duration: '30s', target: 0 },    // Ramp down
  ],

  thresholds: {
    http_req_duration: ["p(95)<500"],
    purchase_success: ["rate>0"],
  },
};

// ... resto do código igual ao ticket-system-k6.js
```

Execute:
```bash
k6 run ticket-system-k6-stress.js
```

---

## Recomendação para Desenvolvimento Local

**Melhor abordagem**: Combine Solução 1 (temporária) + Solução 2:

```bash
# 1. Aumentar limite na sessão atual
ulimit -n 10000

# 2. Serviços já estão configurados com limites razoáveis

# 3. Executar teste com ramp-up
k6 run ticket-system-k6-stress.js
```

---

## Verificar Se o Problema Foi Resolvido

```bash
# 1. Verificar limite atual
ulimit -n
# Deve mostrar 10000 ou mais

# 2. Executar teste
k6 run ticket-system-k6.js

# 3. Verificar logs dos serviços
# Não deve mostrar "Too many open files"
```

---

## Para Produção (Docker/Kubernetes)

### Docker

Adicione ao `docker-compose.yml`:

```yaml
services:
  vacancy-service:
    # ... configuração existente ...
    ulimits:
      nofile:
        soft: 65536
        hard: 65536

  ticket-service:
    # ... configuração existente ...
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

### Kubernetes

Adicione ao pod spec:

```yaml
spec:
  containers:
  - name: vacancy-service
    # ... configuração existente ...
    resources:
      limits:
        cpu: "1"
        memory: "512Mi"
      requests:
        cpu: "500m"
        memory: "256Mi"
    securityContext:
      capabilities:
        add:
        - SYS_RESOURCE
```

---

## Limites Recomendados por Ambiente

| Ambiente | ulimit -n | Workers | Max Connections |
|----------|-----------|---------|-----------------|
| **Dev Local** | 10,000 | 1 | 50 |
| **Staging** | 65,536 | 2-4 | 100 |
| **Production** | 200,000 | 4-8 | 200 |

---

## Monitoramento

Adicione logging para detectar o problema:

```python
# src/common/logging.py
import resource

def log_system_limits(logger):
    """Log current system resource limits."""
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    logger.info(f"File descriptor limits: soft={soft}, hard={hard}")
```

Use no startup:

```python
# src/vacancy/main.py
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Vacancy Service on port {settings.vacancy_port}")
    logger.info(f"Initial stock: {settings.initial_stock}")

    # Log system limits
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    logger.info(f"File descriptor limits: soft={soft}, hard={hard}")
```

---

## Debug: Verificar File Descriptors em Uso

```bash
# Contar file descriptors abertos pelo processo Python
lsof -p <PID> | wc -l

# Encontrar PID do processo
ps aux | grep "run_vacancy.py"

# Monitorar em tempo real
watch -n 1 "lsof -p <PID> | wc -l"
```

---

## Resumo - Quick Fix

```bash
# 1. Aumentar limite (copiar e colar)
ulimit -n 10000

# 2. Verificar
ulimit -n

# 3. Reiniciar serviços
# Terminal 1
python scripts/run_vacancy.py

# Terminal 2
python scripts/run_ticket.py

# 4. Executar teste
k6 run ticket-system-k6.js
```

Se o problema persistir com 200 VUs, use ramp-up gradual ou reduza a carga simultânea.
