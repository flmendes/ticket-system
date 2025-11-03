# Kubernetes Autoscaling Guide

Este guia explica como funciona o autoscaling automático dos pods baseado em carga (CPU e memória) no cluster Kubernetes.

---

## 🎯 Overview

O sistema está configurado com **HorizontalPodAutoscaler (HPA)** que automaticamente ajusta o número de réplicas dos pods baseado em métricas de CPU e memória.

### Características

- ✅ **Autoscaling baseado em CPU** - Target: 70% de utilização
- ✅ **Autoscaling baseado em Memória** - Target: 80% de utilização
- ✅ **Escala automática**: 2 (mínimo) → 10 (máximo) réplicas
- ✅ **Scale-up rápido**: Até 100% em 30s ou 4 pods
- ✅ **Scale-down conservador**: Máximo 50% em 60s após 5min de estabilidade

---

## 📊 Configuração Atual

### Ticket Service HPA

```yaml
Min Replicas: 2
Max Replicas: 10
Target CPU: 70%
Target Memory: 80%
```

### Vacancy Service HPA

```yaml
Min Replicas: 2
Max Replicas: 10
Target CPU: 70%
Target Memory: 80%
```

### Políticas de Scaling

**Scale Up (Aumentar pods)**:
- ⚡ **Imediato** - Sem janela de estabilização
- 📈 **Agressivo** - Até 100% de aumento a cada 30s
- 🚀 **Ou** - Adiciona até 4 pods a cada 30s
- 🎯 **Escolhe o maior** entre os dois valores

**Scale Down (Reduzir pods)**:
- ⏳ **Conservador** - Aguarda 5 minutos de estabilidade
- 📉 **Gradual** - Máximo 50% de redução a cada 60s
- 🐌 **Ou** - Remove no máximo 2 pods a cada 60s
- 🎯 **Escolhe o menor** entre os dois valores

---

## 🚀 Como Usar

### Ver Status do HPA

```bash
# Via Makefile
make hpa-status

# Direto com kubectl
kubectl get hpa -n ticket-system
```

**Output**:
```
NAME                  REFERENCE                    TARGETS                        MINPODS   MAXPODS   REPLICAS
ticket-service-hpa    Deployment/ticket-service    cpu: 4%/70%, memory: 77%/80%   2         10        2
vacancy-service-hpa   Deployment/vacancy-service   cpu: 3%/70%, memory: 74%/80%   2         10        2
```

### Monitorar Scaling em Tempo Real

```bash
# Via Makefile (requer 'watch' instalado)
make watch-hpa

# Ou manualmente
watch -n 2 'kubectl get hpa -n ticket-system && echo "" && kubectl get pods -n ticket-system'
```

### Ver Métricas dos Pods

```bash
kubectl top pods -n ticket-system
```

**Output**:
```
NAME                              CPU(cores)   MEMORY(bytes)
ticket-service-xxx                4m           101Mi
ticket-service-yyy                4m           96Mi
vacancy-service-xxx               3m           97Mi
vacancy-service-yyy               4m           92Mi
```

---

## 🧪 Testar Autoscaling

### Teste Rápido com Hey

```bash
# Gerar carga por 60 segundos com 50 conexões concorrentes
hey -z 60s -c 50 -m POST \
  -H "Content-Type: application/json" \
  -d '{"qty":1}' \
  http://ticket.127.0.0.1.nip.io/api/v1/purchase

# Em outro terminal, monitorar
make watch-hpa
```

### Teste Completo com K6

```bash
# Teste de 17 minutos que escala de 0 → 150 VUs
k6 run ticket-system-k6-autoscaling.js

# Monitorar em outro terminal
kubectl get hpa -n ticket-system -w
```

**Fases do teste K6**:
1. **0-1min**: Warm-up com 10 VUs (baseline)
2. **1-3min**: Aumenta para 50 VUs (trigger scaling)
3. **3-6min**: Aumenta para 100 VUs (scale to ~6-8 pods)
4. **6-8min**: Peak de 150 VUs (scale to max ~10 pods)
5. **8-11min**: Sustenta 150 VUs (verificar estabilidade)
6. **11-17min**: Reduz gradualmente (observe scale down)

---

## 📈 Comportamento Observado

### Teste Real - 60s com 50 conexões

**Início** (antes da carga):
```
ticket-service:  2 pods, CPU 3%, Memory 77%
vacancy-service: 2 pods, CPU 3%, Memory 74%
```

**Durante a carga** (após 30s):
```
ticket-service:  10 pods, CPU 184%, Memory 80%  ← Escalou para máximo!
vacancy-service: 8 pods,  CPU 149%, Memory 76%  ← Escalou para 8!
```

**Resultados**:
- 📊 **63,464 requests** processados em 60s
- 🚀 **1,056 req/s** de throughput
- ✅ **0% de erros** - 100% success rate
- ⚡ **P95 latency**: 219ms (aceitável durante scaling)
- 📈 **Scaling**: 2 → 10 pods (ticket) e 2 → 8 pods (vacancy)

**Após a carga** (scale down):
- ⏳ Aguarda 5 minutos de estabilidade
- 📉 Reduz gradualmente 50% a cada 60s
- 🎯 Retorna para 2 pods em ~10 minutos

---

## 🔍 Entendendo as Métricas

### CPU Utilization

```
cpu: 184%/70%
     ^^^  ^^
     |    |
     |    └─ Target (70%)
     └────── Atual (184% = muito acima do target)
```

**Interpretação**:
- **< 70%**: Dentro do target, sem escalar
- **> 70%**: Acima do target, **SCALE UP** necessário
- **> 100%**: Pods sobrecarregados, scale up urgente

### Memory Utilization

```
memory: 85%/80%
        ^^  ^^
        |   |
        |   └─ Target (80%)
        └───── Atual (85% = acima do target)
```

**Interpretação**:
- **< 80%**: Dentro do target
- **> 80%**: Acima do target, **SCALE UP** necessário
- **> 90%**: Risco de OOM (Out of Memory)

---

## 🎯 Quando o HPA Escala

### Scale Up (Adiciona Pods)

O HPA adiciona pods quando:

1. **CPU ou Memory acima do target** por ~15-30 segundos
2. **Exemplo**: CPU atual 184% > 70% target
3. **Cálculo**: Desired = Current × (Current / Target)
   - Current: 2 pods com 184% CPU
   - Desired: 2 × (184 / 70) = 5.26 → arredonda para 6 pods
   - Políticas: Pode adicionar até 4 pods a cada 30s
   - Resultado: Escala para 6 pods (de 2)

4. **Próximo ciclo** (30s depois):
   - Se ainda acima de 70%, adiciona mais pods
   - Continua até atingir maxReplicas (10) ou ficar abaixo do target

### Scale Down (Remove Pods)

O HPA remove pods quando:

1. **CPU e Memory abaixo do target** por **5 minutos** (stabilizationWindow)
2. **Exemplo**: CPU atual 20% < 70% target
3. **Aguarda**: 5 minutos de estabilidade para evitar flapping
4. **Cálculo**: Similar ao scale up, mas com políticas mais conservadoras
5. **Reduz**: Máximo 50% ou 2 pods a cada 60s
6. **Continua**: Até atingir minReplicas (2)

---

## 🛠️ Troubleshooting

### HPA mostra "<unknown>" nas métricas

**Problema**:
```
TARGETS: cpu: <unknown>/70%, memory: <unknown>/80%
```

**Causas**:
1. Metrics-server não está rodando
2. Metrics-server ainda coletando dados (aguarde 30-60s)
3. Pods sem resource requests definidos

**Solução**:
```bash
# Verificar metrics-server
kubectl get pods -n kube-system | grep metrics

# Verificar se está coletando métricas
kubectl top nodes
kubectl top pods -n ticket-system

# Se não funcionar, reinstalar
kubectl delete deployment metrics-server -n kube-system
# Executar make install-metrics-server
```

### HPA não está escalando

**Problema**: Carga alta mas pods não aumentam

**Verificar**:
```bash
# 1. Ver eventos do HPA
kubectl describe hpa -n ticket-system ticket-service-hpa

# 2. Ver métricas atuais
kubectl top pods -n ticket-system

# 3. Ver resource requests/limits
kubectl describe pod -n ticket-system <pod-name> | grep -A5 Requests
```

**Causas comuns**:
1. CPU/Memory não ultrapassaram o target
2. Já está no maxReplicas
3. Metrics-server com problemas
4. Requests não definidos nos pods

### Pods escalando demais (flapping)

**Problema**: Pods ficam aumentando/diminuindo constantemente

**Causa**: Janela de estabilização muito curta

**Solução**: Ajustar `stabilizationWindowSeconds` no HPA:
```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 600  # Aumentar para 10min
```

---

## 📊 Arquivos Relacionados

| Arquivo | Descrição |
|---------|-----------|
| `k8s/vacancy-hpa.yaml` | HPA para vacancy service |
| `k8s/ticket-hpa.yaml` | HPA para ticket service |
| `k8s/vacancy-deployment-registry.yaml` | Deployment com resource requests |
| `k8s/ticket-deployment-registry.yaml` | Deployment com resource requests |
| `ticket-system-k6-autoscaling.js` | Teste K6 para autoscaling |

---

## ⚙️ Configurações Avançadas

### Alterar Targets de CPU/Memory

Editar o HPA:
```bash
kubectl edit hpa ticket-service-hpa -n ticket-system
```

Mudar valores:
```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70  # Mudar aqui (50-80 recomendado)
```

### Alterar Min/Max Replicas

```bash
kubectl patch hpa ticket-service-hpa -n ticket-system -p '{"spec":{"minReplicas":3,"maxReplicas":20}}'
```

### Alterar Comportamento de Scaling

Editar políticas em `k8s/ticket-hpa.yaml`:
```yaml
behavior:
  scaleUp:
    stabilizationWindowSeconds: 0     # Imediato
    policies:
    - type: Percent
      value: 200                      # Dobrar a cada ciclo
      periodSeconds: 15                # A cada 15s
```

---

## 📈 Métricas Customizadas (Futuro)

Além de CPU e Memory, você pode escalar baseado em:

### Requisições por Segundo (RPS)

```yaml
metrics:
- type: Pods
  pods:
    metric:
      name: http_requests_per_second
    target:
      type: AverageValue
      averageValue: "100"  # 100 req/s por pod
```

### Latência

```yaml
metrics:
- type: Pods
  pods:
    metric:
      name: http_request_duration_seconds
    target:
      type: AverageValue
      averageValue: "0.1"  # 100ms
```

**Requer**: Prometheus + Custom Metrics API

---

## 🎓 Best Practices

### 1. Sempre Defina Resource Requests

```yaml
resources:
  requests:
    memory: "128Mi"  # OBRIGATÓRIO para HPA
    cpu: "100m"      # OBRIGATÓRIO para HPA
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 2. Teste Antes de Produção

```bash
# Testar com carga sintética
make load-test

# Monitorar comportamento
make watch-hpa
```

### 3. Configure Alertas

- ⚠️ Alerta quando pods = maxReplicas (capacidade máxima)
- ⚠️ Alerta quando CPU > 90% por 5min (insuficiente)
- ⚠️ Alerta quando HPA não consegue escalar

### 4. Ajuste Conservadoramente

- Comece com targets altos (70-80%)
- Observe por dias/semanas
- Ajuste baseado em dados reais
- Evite over-provisioning

### 5. Combine com Cluster Autoscaler

Para produção, combine HPA (pods) com Cluster Autoscaler (nodes):
- HPA: Aumenta pods até maxReplicas
- CA: Se nodes sem capacidade, adiciona nodes
- Resultado: Escalabilidade ilimitada (até limites de cloud)

---

## 📊 Monitoramento em Produção

### Métricas para Observar

1. **HPA Metrics**:
   ```bash
   kubectl get hpa -n ticket-system -o yaml
   ```

2. **Pod Scaling Events**:
   ```bash
   kubectl get events -n ticket-system --sort-by='.lastTimestamp'
   ```

3. **Resource Utilization**:
   ```bash
   kubectl top pods -n ticket-system --containers
   ```

### Grafana Dashboards

Métricas úteis para Prometheus/Grafana:
- `kube_hpa_status_current_replicas`
- `kube_hpa_status_desired_replicas`
- `kube_hpa_spec_max_replicas`
- `kube_pod_container_resource_requests_cpu_cores`
- `kube_pod_container_resource_limits_cpu_cores`

---

## 🎯 Comandos Rápidos

```bash
# Ver status
make hpa-status

# Monitorar em tempo real
make watch-hpa

# Descrever HPA (ver eventos)
kubectl describe hpa ticket-service-hpa -n ticket-system

# Ver últimos eventos de scaling
kubectl get events -n ticket-system | grep -i scale

# Forçar scaling manual (teste)
kubectl scale deployment ticket-service -n ticket-system --replicas=5

# Deletar HPA (volta para réplicas fixas)
kubectl delete hpa -n ticket-system --all
```

---

## 🔧 Makefile Commands

```bash
make deploy-hpa      # Deploy HPAs
make hpa-status      # Ver status e métricas
make watch-hpa       # Monitorar em tempo real
```

---

## 📝 Exemplo Completo

### Cenário: Black Friday

**Preparação**:
```bash
# 1. Verificar HPAs configurados
make hpa-status

# 2. Aumentar maxReplicas para demanda
kubectl patch hpa ticket-service-hpa -n ticket-system \
  -p '{"spec":{"maxReplicas":20}}'
```

**Durante o evento**:
```bash
# Monitorar em tempo real
make watch-hpa
```

**Comportamento esperado**:
- **08:00**: 2 pods (baseline)
- **09:00**: Início das vendas, CPU sobe
- **09:02**: HPA escala para 6 pods
- **09:05**: HPA escala para 10 pods
- **09:10**: HPA escala para 15 pods (pico)
- **12:00**: Vendas caem, CPU baixa
- **12:05**: HPA começa scale down
- **12:15**: Retorna para 4-6 pods
- **18:00**: Retorna para 2 pods (baseline)

---

## ✅ Validação

Sistema com autoscaling está OK quando:

- ✅ `make hpa-status` mostra métricas válidas (não `<unknown>`)
- ✅ TARGETS mostram CPU e Memory com valores percentuais
- ✅ REPLICAS está entre MINPODS e MAXPODS
- ✅ Sob carga, REPLICAS aumenta automaticamente
- ✅ Sem carga, REPLICAS volta para MINPODS

---

**Versão**: 1.0.0
**Última atualização**: 2025-11-02
**Testado**: ✅ Funcionando perfeitamente (2 → 10 pods em 60s)
