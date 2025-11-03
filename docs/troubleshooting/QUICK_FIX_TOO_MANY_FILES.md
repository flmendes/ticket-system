# Quick Fix: "Too many open files" - macOS

## 🚨 Erro

```
OSError: [Errno 24] Too many open files
```

---

## ✅ Solução Rápida (3 passos)

### 1️⃣ Aumentar limite do sistema (copiar e colar)

```bash
# Verificar limite atual
ulimit -n

# Aumentar para 10,000
ulimit -n 10000

# Confirmar
ulimit -n
```

> ⚠️ **Nota**: Este comando funciona apenas na sessão atual do terminal.
> Você precisará executá-lo novamente se abrir um novo terminal.

---

### 2️⃣ Reiniciar os serviços

Os scripts já foram atualizados com configurações de limite de concorrência.

```bash
# Parar serviços atuais (Ctrl+C em cada terminal)

# Terminal 1 - Vacancy Service
python scripts/run_vacancy.py

# Terminal 2 - Ticket Service
python scripts/run_ticket.py
```

---

### 3️⃣ Executar teste com Ramp-up Gradual

**NOVO**: Use o script com ramp-up gradual em vez de 200 VUs instantâneos:

```bash
# Ao invés de:
# k6 run ticket-system-k6.js (100 VUs instantâneos)

# Use:
k6 run ticket-system-k6-stress.js
```

Este script sobe gradualmente:
- 0 → 50 VUs (30s)
- 50 → 100 VUs (30s)
- 100 → 150 VUs (30s)
- 150 → 200 VUs (30s)
- Mantém 200 VUs por 2 minutos
- Ramp-down para 0

---

## 🎯 O Que Foi Mudado

### Scripts Python (run_vacancy.py, run_ticket.py)

Adicionado configurações uvicorn:

```python
uvicorn.run(
    # ... existente ...
    workers=1,                    # Workers
    backlog=2048,                 # Fila de conexões
    limit_concurrency=500,        # Limite de requisições simultâneas
    timeout_keep_alive=5,         # Keep-alive timeout
)
```

### Docker Compose

Adicionado limites de file descriptors:

```yaml
ulimits:
  nofile:
    soft: 65536
    hard: 65536
```

### Novo Script K6

Criado `ticket-system-k6-stress.js` com ramp-up gradual.

---

## 🧪 Testar a Correção

```bash
# 1. Verificar limite
ulimit -n
# Deve mostrar 10000

# 2. Iniciar serviços (em 2 terminais diferentes)
python scripts/run_vacancy.py
python scripts/run_ticket.py

# 3. Executar stress test
k6 run ticket-system-k6-stress.js

# 4. Verificar logs - não deve ter "Too many open files"
```

---

## 📊 Limites Configurados

| Item | Valor | Descrição |
|------|-------|-----------|
| **ulimit -n** | 10,000 | File descriptors (macOS) |
| **uvicorn workers** | 1 | Workers (dev) |
| **uvicorn backlog** | 2,048 | Fila de conexões |
| **limit_concurrency** | 500 | Requisições simultâneas |
| **Docker ulimits** | 65,536 | File descriptors (containers) |

---

## 🔧 Para Tornar Permanente (Opcional)

Se você quiser que o limite seja permanente:

### Opção 1: Adicionar ao ~/.zshrc ou ~/.bashrc

```bash
# Abrir arquivo
nano ~/.zshrc  # ou ~/.bashrc se usar bash

# Adicionar linha
ulimit -n 10000

# Salvar (Ctrl+X, Y, Enter)

# Aplicar
source ~/.zshrc
```

### Opção 2: Configuração do Sistema (macOS)

Ver instruções completas em: **TROUBLESHOOTING.md**

---

## ❓ FAQ

### Q: Por que acontece?

Cada conexão HTTP usa um file descriptor. Com 200 VUs fazendo requisições, você facilmente ultrapassa o limite padrão do macOS (256 ou 512).

### Q: É seguro aumentar o limite?

Sim, 10,000 é um valor conservador e seguro para desenvolvimento local.

### Q: Preciso fazer isso toda vez?

Se usar a Solução Rápida (ulimit -n 10000), sim, em cada nova sessão de terminal.
Para tornar permanente, use as Opções 1 ou 2 acima.

### Q: E em produção (Docker/Kubernetes)?

O `docker-compose.yml` já foi atualizado com `ulimits`. Para Kubernetes, veja TROUBLESHOOTING.md.

---

## 📖 Mais Informações

Para soluções mais detalhadas e configurações avançadas:

👉 **TROUBLESHOOTING.md** - Guia completo

---

## ✅ Checklist

- [ ] Executei `ulimit -n 10000`
- [ ] Verifiquei com `ulimit -n` (mostra 10000)
- [ ] Reiniciei os serviços Python
- [ ] Usei `ticket-system-k6-stress.js` (com ramp-up)
- [ ] Teste passou sem erros "Too many open files"

---

**Última atualização**: 2025-11-02
