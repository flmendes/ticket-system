# Kubernetes Deployment Guide - Ticket System

## 📋 Overview

Este diretório contém os manifestos Kubernetes para fazer deploy do ticket-system em um cluster Kubernetes local (kind).

## 🚀 Quick Deploy

### 1. Build Docker Images

```bash
# Build vacancy service
docker build -f Dockerfile.vacancy -t vacancy-service:latest .

# Build ticket service
docker build -f Dockerfile.ticket -t ticket-service:latest .
```

### 2. Load Images into Kind Cluster

```bash
# Load images into kind
kind load docker-image vacancy-service:latest --name kind
kind load docker-image ticket-service:latest --name kind
```

### 3. Install Nginx Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### 4. Deploy Ticket System

```bash
# Apply manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/vacancy-deployment.yaml
kubectl apply -f k8s/ticket-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

### 5. Verify Deployment

```bash
# Check all resources
kubectl get all -n ticket-system

# Check Redis
kubectl get pods -n ticket-system -l app=redis
kubectl logs -n ticket-system deployment/redis

# Check ingress
kubectl get ingress -n ticket-system

# Check logs
kubectl logs -n ticket-system deployment/ticket-service
kubectl logs -n ticket-system deployment/vacancy-service
```

## 🌐 Access

O ticket service está exposto via Ingress no seguinte endereço:

**Base URL**: http://ticket.127.0.0.1.nip.io/

### Available Endpoints

```bash
# Root endpoint - Service info
curl http://ticket.127.0.0.1.nip.io/

# Health check
curl http://ticket.127.0.0.1.nip.io/api/v1/health

# Purchase tickets
curl -X POST http://ticket.127.0.0.1.nip.io/api/v1/purchase \
  -H "Content-Type: application/json" \
  -d '{"qty": 5}'

# API Documentation
open http://ticket.127.0.0.1.nip.io/docs
```

## 📁 Manifest Files

### `namespace.yaml`
Cria o namespace `ticket-system` para isolar os recursos.

### `configmap.yaml`
ConfigMap com todas as variáveis de ambiente:
- Deployment mode: microservices
- Service ports: 8001 (vacancy), 8002 (ticket)
- Redis configuration: host, port, connection settings
- Stock configuration: 10000 initial tickets
- HTTP client settings
- Logging configuration

### `redis-deployment.yaml`
Redis database para distributed locking e gerenciamento de estoque:
- Redis 7-alpine para otimização
- Persistent volume para dados
- Health checks configurados
- Resources limits definidos
- Service ClusterIP para comunicação interna

### `vacancy-deployment.yaml`
- **Deployment**: 2 replicas
- **Resources**: 128Mi-512Mi RAM, 100m-500m CPU
- **Health checks**: Liveness + Readiness probes
- **Service**: ClusterIP on port 8001

### `ticket-deployment.yaml`
- **Deployment**: 2 replicas
- **Resources**: 128Mi-512Mi RAM, 100m-500m CPU
- **Health checks**: Liveness + Readiness probes
- **Service**: ClusterIP on port 8002

### `ingress.yaml`
- **IngressClass**: nginx
- **Host**: ticket.127.0.0.1.nip.io
- **Backend**: ticket-service:8002

## 🔍 Monitoring

### Check Pod Status

```bash
kubectl get pods -n ticket-system

# Expected output:
# NAME                              READY   STATUS    RESTARTS   AGE
# ticket-service-xxx                1/1     Running   0          Xm
# ticket-service-yyy                1/1     Running   0          Xm
# vacancy-service-xxx               1/1     Running   0          Xm
# vacancy-service-yyy               1/1     Running   0          Xm
```

### View Logs

```bash
# Ticket service logs
kubectl logs -n ticket-system -l app=ticket-service --tail=50

# Vacancy service logs
kubectl logs -n ticket-system -l app=vacancy-service --tail=50

# Follow logs in real-time
kubectl logs -n ticket-system -l app=ticket-service -f
```

### Describe Resources

```bash
# Describe pods
kubectl describe pod -n ticket-system -l app=ticket-service

# Describe services
kubectl describe svc -n ticket-system

# Describe ingress
kubectl describe ingress -n ticket-system ticket-system-ingress
```

## 🛠️ Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n ticket-system

# Check pod events
kubectl describe pod -n ticket-system <pod-name>

# Check logs
kubectl logs -n ticket-system <pod-name>
```

### Image pull errors

Certifique-se que as imagens foram carregadas no kind:

```bash
# List images in kind node
docker exec -it kind-control-plane crictl images | grep service
```

### Ingress not working

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress configuration
kubectl describe ingress -n ticket-system ticket-system-ingress

# Test internal service
kubectl run -n ticket-system test-curl \
  --image=curlimages/curl:latest --rm -it --restart=Never \
  -- curl http://ticket-service:8002/
```

### Services not communicating

```bash
# Test vacancy service from within cluster
kubectl run -n ticket-system test-curl \
  --image=curlimages/curl:latest --rm -it --restart=Never \
  -- curl http://vacancy-service:8001/api/v1/available

# Check DNS resolution
kubectl run -n ticket-system test-dns \
  --image=busybox:latest --rm -it --restart=Never \
  -- nslookup vacancy-service
```

## 🔄 Update Deployment

### Update ConfigMap

```bash
# Edit configmap
kubectl edit configmap -n ticket-system ticket-system-config

# Or apply updated file
kubectl apply -f k8s/configmap.yaml

# Restart deployments to pick up changes
kubectl rollout restart deployment -n ticket-system ticket-service
kubectl rollout restart deployment -n ticket-system vacancy-service
```

### Update Docker Images

```bash
# Rebuild images
docker build -f Dockerfile.vacancy -t vacancy-service:latest .
docker build -f Dockerfile.ticket -t ticket-service:latest .

# Reload into kind
kind load docker-image vacancy-service:latest --name kind
kind load docker-image ticket-service:latest --name kind

# Restart deployments
kubectl rollout restart deployment -n ticket-system
```

### Scale Deployments

```bash
# Scale vacancy service
kubectl scale deployment -n ticket-system vacancy-service --replicas=3

# Scale ticket service
kubectl scale deployment -n ticket-system ticket-service --replicas=3

# Auto-scale (requires metrics-server)
kubectl autoscale deployment -n ticket-system ticket-service \
  --cpu-percent=80 --min=2 --max=10
```

## 🗑️ Cleanup

### Delete All Resources

```bash
# Delete namespace (removes all resources)
kubectl delete namespace ticket-system

# Or delete individual manifests
kubectl delete -f k8s/ingress.yaml
kubectl delete -f k8s/ticket-deployment.yaml
kubectl delete -f k8s/vacancy-deployment.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/namespace.yaml
```

### Remove Images from Kind

```bash
# Images remain in kind even after deleting deployments
# To completely clean up, recreate the cluster
kind delete cluster --name kind
kind create cluster --name kind
```

## 📊 Architecture in Kubernetes

```
                     Internet
                        │
                        ↓
              ┌─────────────────┐
              │  Nginx Ingress  │
              │   Controller    │
              └────────┬────────┘
                       │
         ticket.127.0.0.1.nip.io
                       │
                       ↓
              ┌─────────────────┐
              │ Ticket Service  │ ← ClusterIP (8002)
              │   (2 replicas)  │
              └────────┬────────┘
                       │ HTTP
                       ↓
              ┌─────────────────┐
              │ Vacancy Service │ ← ClusterIP (8001)
              │   (2 replicas)  │
              └─────────────────┘
```

## 📝 Notes

- **ImagePullPolicy**: Set to `Never` for local kind images
- **Service Type**: ClusterIP (internal only, exposed via Ingress)
- **Replicas**: 2 pods per service for high availability
- **Health Checks**: Both liveness and readiness probes configured
- **Resources**: Requests and limits defined for proper scheduling
- **nip.io**: Magic DNS service that resolves to the IP in the hostname

## 🎯 Production Considerations

Para deployment em produção, considere:

1. **Persistent Storage**: Usar StatefulSet ou banco de dados externo para estoque
2. **Secrets**: Mover credenciais para Kubernetes Secrets
3. **Resource Limits**: Ajustar baseado em testes de carga
4. **Horizontal Pod Autoscaling**: Configurar HPA baseado em métricas
5. **Network Policies**: Restringir comunicação entre pods
6. **TLS/SSL**: Adicionar certificados para HTTPS
7. **Monitoring**: Integrar com Prometheus/Grafana
8. **Logging**: Centralizar logs com ELK ou similar
9. **Service Mesh**: Considerar Istio/Linkerd para observabilidade avançada

---

**Deployment Date**: 2025-11-03
**Version**: 1.0.0
**Environment**: Development (kind)
