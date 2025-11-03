# Makefile Guide - Automated Build & Deploy

Este guia explica como usar o Makefile para automatizar o build, push para registry local e deploy no Kubernetes.

---

## 🎯 Pré-requisitos

1. **Docker Registry Local** rodando na porta 5001:5000
   ```bash
   # Verificar se o registry está rodando
   curl http://localhost:5001/v2/_catalog
   ```

2. **Kind cluster** configurado e rodando
   ```bash
   kind get clusters
   ```

3. **Nginx Ingress Controller** instalado no cluster
   ```bash
   kubectl get pods -n ingress-nginx
   ```

4. **Ferramentas instaladas**:
   - `make`
   - `docker`
   - `kubectl`
   - `jq` (para testes)
   - `k6` (opcional, para load testing)

---

## 🚀 Quick Start

### Deploy Completo (do Zero)

```bash
# Build, push e deploy tudo de uma vez
make full-deploy
```

Este comando executa:
1. ✅ Verifica se o registry está acessível
2. 🔨 Build das imagens Docker
3. 🏷️  Tag das imagens para o registry local
4. 📤 Push das imagens para o registry
5. 🚀 Deploy no Kubernetes
6. ⏳ Aguarda os pods ficarem prontos
7. 📊 Mostra o status do deployment

**Output esperado**:
```
╔══════════════════════════════════════════════╗
║  ✅ Full deployment completed successfully! ║
╚══════════════════════════════════════════════╝

🌐 Access the application at:
   http://ticket.127.0.0.1.nip.io/

📚 View API docs at:
   http://ticket.127.0.0.1.nip.io/docs
```

---

## 📚 Comandos Disponíveis

### Help

```bash
make help
# ou simplesmente
make
```

Mostra todos os comandos disponíveis com descrições.

---

### Build

```bash
# Build de todas as imagens
make build

# Build individual
make build-vacancy
make build-ticket
```

Compila as imagens Docker usando os Dockerfiles existentes.

---

### Tag & Push

```bash
# Tag e push de todas as imagens
make push

# Tag individual
make tag-vacancy
make tag-ticket

# Push individual
make push-vacancy
make push-ticket
```

Tagueia as imagens para o registry local (`localhost:5001/ticket-system/`) e faz push.

---

### Deploy

```bash
# Deploy completo
make deploy

# Deploy por componente
make deploy-namespace    # Cria namespace
make deploy-configmap    # Aplica ConfigMap
make deploy-services     # Deploya os serviços
make deploy-ingress      # Configura Ingress
```

Aplica os manifestos Kubernetes no cluster.

---

### Status & Monitoring

```bash
# Status geral
make status

# Logs de todos os serviços (últimas 20 linhas)
make logs

# Logs em tempo real
make logs-vacancy    # Vacancy service
make logs-ticket     # Ticket service

# Descrever pods (para debug)
make describe-pods
```

---

### Testes

```bash
# Testes rápidos (health, info, purchase)
make test

# Load test com K6
make load-test
```

**Output do `make test`**:
```json
1. Health Check:
{
  "status": "healthy",
  "service": "ticket"
}

2. Service Info:
{
  "service": "ticket-service",
  "version": "1.0.0",
  "status": "operational"
}

3. Purchase Test:
{
  "success": true,
  "remaining": 9999,
  "message": "Purchase successful!"
}
```

---

### Atualização Rápida

```bash
# Rebuild, push e restart (sem recriar recursos)
make update

# Ciclo completo de dev: update + test
make dev
```

**Use `make update` quando**:
- Fez mudanças no código
- Quer atualizar os pods sem destruir o namespace
- Desenvolvimento iterativo rápido

**Diferença entre `update` e `full-deploy`**:
- `update`: Apenas rebuild → push → restart pods
- `full-deploy`: Recria tudo do zero (namespace, configmap, etc)

---

### Operações

```bash
# Restart dos deployments
make restart

# Scale (exemplo: 3 réplicas)
make scale REPLICAS=3

# Port forward para acesso direto
make port-forward-vacancy    # localhost:8001
make port-forward-ticket     # localhost:8002

# Shell nos pods
make shell-vacancy
make shell-ticket
```

---

### Registry

```bash
# Verificar se registry está acessível
make check-registry

# Listar imagens no registry
make registry-images
```

**Output**:
```json
📦 Images in registry:
{
  "repositories": [
    "ticket-system/ticket-service",
    "ticket-system/vacancy-service"
  ]
}

Vacancy service tags:
{
  "name": "ticket-system/vacancy-service",
  "tags": ["latest"]
}
```

---

### Cleanup

```bash
# Deletar recursos do Kubernetes
make clean

# Deletar imagens Docker locais
make clean-images
```

⚠️ **Atenção**: `make clean` deleta o namespace inteiro e todos os recursos.

---

## 🔧 Configuração

### Variáveis de Ambiente

Você pode customizar o comportamento do Makefile com variáveis:

```bash
# Usar registry diferente
make push REGISTRY=meu-registry.local:5000

# Usar versão/tag diferente
make push VERSION=v1.2.3

# Namespace diferente
make deploy NAMESPACE=production

# Combinar múltiplas variáveis
make full-deploy REGISTRY=localhost:5001 VERSION=v2.0.0
```

### Variáveis Disponíveis

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `REGISTRY` | `localhost:5001` | Endereço do registry |
| `VERSION` | `latest` | Tag da imagem |
| `NAMESPACE` | `ticket-system` | Namespace Kubernetes |
| `REPLICAS` | - | Número de réplicas (para `make scale`) |

---

## 📊 Workflows Comuns

### Workflow 1: Primeiro Deploy

```bash
# 1. Verificar registry
make check-registry

# 2. Deploy completo
make full-deploy

# 3. Testar
make test

# 4. Ver status
make status
```

### Workflow 2: Desenvolvimento Iterativo

```bash
# 1. Fazer mudanças no código
vim src/ticket/services.py

# 2. Update rápido
make dev

# Output:
# - Build das imagens
# - Push para registry
# - Restart dos pods
# - Testes automáticos
```

### Workflow 3: Debugging

```bash
# 1. Ver logs em tempo real
make logs-ticket

# 2. Em outro terminal, fazer requests
curl -X POST http://ticket.127.0.0.1.nip.io/api/v1/purchase \
  -H "Content-Type: application/json" \
  -d '{"qty": 1}'

# 3. Se precisar, descrever pods
make describe-pods

# 4. Ou entrar no pod
make shell-ticket
```

### Workflow 4: Load Testing

```bash
# 1. Deploy
make full-deploy

# 2. Aguardar estabilização
sleep 10

# 3. Load test
make load-test

# 4. Monitorar logs durante o teste
make logs
```

### Workflow 5: Scale Up/Down

```bash
# Scale up para 5 réplicas
make scale REPLICAS=5

# Verificar
make status

# Scale down para 2 réplicas
make scale REPLICAS=2
```

### Workflow 6: Atualização de Produção

```bash
# 1. Build com versão específica
make build VERSION=v1.5.0

# 2. Push para registry
make push VERSION=v1.5.0

# 3. Atualizar manifestos manualmente ou usar sed
sed -i '' 's/:latest/:v1.5.0/g' k8s/*-registry.yaml

# 4. Deploy
make deploy

# 5. Aguardar e verificar
make wait
make test
```

---

## 🎯 Targets Úteis por Cenário

### Cenário: "Acabei de clonar o repo"

```bash
make full-deploy
```

### Cenário: "Modifiquei o código e quero testar"

```bash
make dev
```

### Cenário: "Os pods estão crashando"

```bash
make logs
make describe-pods
```

### Cenário: "Quero limpar tudo e começar do zero"

```bash
make clean
make full-deploy
```

### Cenário: "Preciso acessar o serviço diretamente"

```bash
make port-forward-ticket
# Em outro terminal:
curl http://localhost:8002/api/v1/health
```

### Cenário: "Quero ver o que está no registry"

```bash
make registry-images
```

---

## 🏗️ Estrutura de Arquivos

```
ticket-system/
├── Makefile                              # 🎯 Este arquivo
├── Dockerfile.vacancy                    # Build vacancy service
├── Dockerfile.ticket                     # Build ticket service
├── k8s/
│   ├── namespace.yaml                    # Namespace definition
│   ├── configmap.yaml                    # Environment variables
│   ├── vacancy-deployment-registry.yaml  # Vacancy deployment (registry)
│   ├── ticket-deployment-registry.yaml   # Ticket deployment (registry)
│   └── ingress.yaml                      # Ingress configuration
└── src/                                  # Source code
```

---

## 🔍 Troubleshooting

### Problema: "Registry not accessible"

```bash
# Verificar se o registry está rodando
docker ps | grep registry

# Testar acesso
curl http://localhost:5001/v2/_catalog

# Se não estiver rodando, iniciar:
docker run -d -p 5001:5000 --name registry registry:2
```

### Problema: "ImagePullBackOff"

```bash
# Verificar se a imagem existe no registry
make registry-images

# Verificar logs do pod
kubectl describe pod -n ticket-system <pod-name>

# Rebuild e push
make build push
make restart
```

### Problema: "Pods não ficam Ready"

```bash
# Ver logs
make logs

# Descrever pods
make describe-pods

# Verificar health probes
kubectl get pods -n ticket-system -o yaml | grep -A10 Probe
```

### Problema: "Ingress não funciona"

```bash
# Verificar ingress controller
kubectl get pods -n ingress-nginx

# Verificar ingress
kubectl describe ingress -n ticket-system

# Testar acesso direto ao service
make port-forward-ticket
curl http://localhost:8002/api/v1/health
```

---

## 📝 Notas Importantes

1. **Registry Local**: O Makefile assume que o registry está em `localhost:5001`. Se estiver diferente, use `REGISTRY=seu-registry:porta`.

2. **ImagePullPolicy**: Os manifestos `*-registry.yaml` usam `imagePullPolicy: Always` para sempre puxar a versão mais recente do registry.

3. **Versões**: Por padrão usa `latest`. Para produção, use versões específicas: `make push VERSION=v1.0.0`.

4. **Namespace**: Todos os recursos são criados no namespace `ticket-system`. Pode ser alterado com `NAMESPACE=outro-nome`.

5. **Limpeza**: `make clean` remove TODOS os recursos. Use com cuidado.

---

## 🎓 Exemplos Práticos

### Exemplo 1: Deploy Inicial

```bash
$ make full-deploy

🔍 Checking registry at localhost:5001...
✅ Registry is accessible
🔨 Building vacancy service...
✅ Vacancy service built
🔨 Building ticket service...
✅ Ticket service built
🏷️  Tagging vacancy service: localhost:5001/ticket-system/vacancy-service:latest
✅ Vacancy service tagged
📤 Pushing vacancy service to localhost:5001...
✅ Vacancy service pushed
# ... (continua)
✅ Full deployment completed successfully!

🌐 Access the application at:
   http://ticket.127.0.0.1.nip.io/
```

### Exemplo 2: Desenvolvimento Iterativo

```bash
# Editar código
$ vim src/ticket/services.py

# Update rápido
$ make dev

🔨 Building ticket service...
✅ Ticket service built
📤 Pushing ticket service...
✅ Ticket service pushed
🔄 Restarting deployments...
✅ Deployments restarted
⏳ Waiting for deployments...
✅ All deployments ready
🧪 Testing deployment...
✅ All tests passed
```

### Exemplo 3: Scale para Alta Carga

```bash
$ make scale REPLICAS=5

📈 Scaling deployments to 5 replicas...
✅ Deployments scaled

$ make status
Pods:
NAME                              READY   STATUS    RESTARTS   AGE
ticket-service-xxx-1              1/1     Running   0          30s
ticket-service-xxx-2              1/1     Running   0          30s
ticket-service-xxx-3              1/1     Running   0          30s
ticket-service-xxx-4              1/1     Running   0          30s
ticket-service-xxx-5              1/1     Running   0          30s
# ... (5 vacancy pods também)
```

---

## 🎯 Comandos Mais Usados

```bash
# Top 5 comandos para desenvolvimento
make full-deploy    # Primeira vez
make dev            # Desenvolvimento iterativo
make logs-ticket    # Debug
make test           # Validação
make clean          # Limpar tudo
```

---

## 📚 Referências

- **Kubernetes**: k8s/README.md
- **Arquitetura Dual-Mode**: DUAL_MODE_GUIDE.md
- **Resultados de Testes**: K8S_LOAD_TEST_RESULTS.md
- **Guia Geral**: CLAUDE.md

---

**Última atualização**: 2025-11-02
**Versão do Makefile**: 1.0.0
