# Makefile for Ticket System - Kubernetes Deployment
# Build ultra-optimized Docker images, push to local registry, and deploy to Kubernetes
# 
# Images are ultra-optimized using:
# - Multi-stage builds with Distroless runtime
# - Reduced from 213MB to ~77MB (63.8% smaller)
# - Security: distroless images, no shell/OS tools, non-root user
# - Performance: fastest startup and deployment possible

# Configuration
REGISTRY ?= localhost:5001
PROJECT_NAME = ticket-system
VERSION ?= latest
NAMESPACE = ticket-system

# Image names
VACANCY_IMAGE = $(PROJECT_NAME)/vacancy-service
TICKET_IMAGE = $(PROJECT_NAME)/ticket-service

# Full image paths
VACANCY_FULL = $(REGISTRY)/$(VACANCY_IMAGE):$(VERSION)
TICKET_FULL = $(REGISTRY)/$(TICKET_IMAGE):$(VERSION)

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)Ticket System - Makefile Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Build & Deploy:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

.PHONY: all
all: build push deploy ## Build, push and deploy everything
	@echo "$(GREEN)✅ All steps completed successfully!$(NC)"

.PHONY: build
build: build-vacancy build-ticket ## Build all Docker images

.PHONY: build-vacancy
build-vacancy: ## Build ultra-optimized vacancy service image (Distroless-based)
	@echo "$(YELLOW)🔨 Building ultra-optimized vacancy service...$(NC)"
	docker build -f Dockerfile.vacancy -t vacancy-service:latest .
	@echo "$(GREEN)✅ Ultra-optimized vacancy service built (Distroless-based, ~77MB)$(NC)"

.PHONY: build-ticket
build-ticket: ## Build ultra-optimized ticket service image (Distroless-based)
	@echo "$(YELLOW)🔨 Building ultra-optimized ticket service...$(NC)"
	docker build -f Dockerfile.ticket -t ticket-service:latest .
	@echo "$(GREEN)✅ Ultra-optimized ticket service built (Distroless-based, ~77MB)$(NC)"

.PHONY: build-alpine
build-alpine: build-vacancy-alpine build-ticket-alpine ## Build Alpine versions for debugging

.PHONY: build-vacancy-alpine
build-vacancy-alpine: ## Build Alpine vacancy service (for debugging)
	@echo "$(YELLOW)🔨 Building Alpine vacancy service for debugging...$(NC)"
	docker build -f Dockerfile.vacancy.alpine -t vacancy-service:alpine .
	@echo "$(GREEN)✅ Alpine vacancy service built (~82MB, debug tools available)$(NC)"

.PHONY: build-ticket-alpine
build-ticket-alpine: ## Build Alpine ticket service (for debugging)
	@echo "$(YELLOW)🔨 Building Alpine ticket service for debugging...$(NC)"
	docker build -f Dockerfile.ticket.alpine -t ticket-service:alpine .
	@echo "$(GREEN)✅ Alpine ticket service built (~82MB, debug tools available)$(NC)"

.PHONY: tag
tag: tag-vacancy tag-ticket ## Tag images for local registry

.PHONY: tag-vacancy
tag-vacancy: ## Tag vacancy service for registry
	@echo "$(YELLOW)🏷️  Tagging vacancy service: $(VACANCY_FULL)$(NC)"
	docker tag vacancy-service:latest $(VACANCY_FULL)
	@echo "$(GREEN)✅ Vacancy service tagged$(NC)"

.PHONY: tag-ticket
tag-ticket: ## Tag ticket service for registry
	@echo "$(YELLOW)🏷️  Tagging ticket service: $(TICKET_FULL)$(NC)"
	docker tag ticket-service:latest $(TICKET_FULL)
	@echo "$(GREEN)✅ Ticket service tagged$(NC)"

.PHONY: push
push: tag push-vacancy push-ticket ## Push images to local registry

.PHONY: push-vacancy
push-vacancy: tag-vacancy ## Push vacancy service to registry
	@echo "$(YELLOW)📤 Pushing vacancy service to $(REGISTRY)...$(NC)"
	docker push $(VACANCY_FULL)
	@echo "$(GREEN)✅ Vacancy service pushed$(NC)"

.PHONY: push-ticket
push-ticket: tag-ticket ## Push ticket service to registry
	@echo "$(YELLOW)📤 Pushing ticket service to $(REGISTRY)...$(NC)"
	docker push $(TICKET_FULL)
	@echo "$(GREEN)✅ Ticket service pushed$(NC)"

.PHONY: check-registry
check-registry: ## Check if registry is accessible
	@echo "$(YELLOW)🔍 Checking registry at $(REGISTRY)...$(NC)"
	@curl -s http://$(REGISTRY)/v2/_catalog > /dev/null && \
		echo "$(GREEN)✅ Registry is accessible$(NC)" || \
		(echo "$(RED)❌ Registry not accessible at $(REGISTRY)$(NC)" && exit 1)

.PHONY: deploy
deploy: deploy-namespace deploy-configmap deploy-redis deploy-services deploy-ingress deploy-hpa ## Deploy to Kubernetes

.PHONY: deploy-namespace
deploy-namespace: ## Create namespace
	@echo "$(YELLOW)📦 Creating namespace...$(NC)"
	kubectl apply -f k8s/namespace.yaml
	@echo "$(GREEN)✅ Namespace created$(NC)"

.PHONY: deploy-configmap
deploy-configmap: ## Deploy ConfigMap
	@echo "$(YELLOW)⚙️  Deploying ConfigMap...$(NC)"
	kubectl apply -f k8s/configmap.yaml
	@echo "$(GREEN)✅ ConfigMap deployed$(NC)"

.PHONY: deploy-redis
deploy-redis: ## Deploy Redis database
	@echo "$(YELLOW)🗄️  Deploying Redis...$(NC)"
	kubectl apply -f k8s/redis-deployment.yaml
	@echo "$(GREEN)✅ Redis deployed$(NC)"

.PHONY: deploy-services
deploy-services: ## Deploy microservices
	@echo "$(YELLOW)🚀 Deploying services...$(NC)"
	kubectl apply -f k8s/vacancy-deployment-registry.yaml
	kubectl apply -f k8s/ticket-deployment-registry.yaml
	@echo "$(GREEN)✅ Services deployed$(NC)"

.PHONY: deploy-ingress
deploy-ingress: ## Deploy Ingress
	@echo "$(YELLOW)🌐 Deploying Ingress...$(NC)"
	kubectl apply -f k8s/ingress.yaml
	@echo "$(GREEN)✅ Ingress deployed$(NC)"

.PHONY: deploy-hpa
deploy-hpa: ## Deploy HorizontalPodAutoscalers
	@echo "$(YELLOW)📈 Deploying HPAs...$(NC)"
	kubectl apply -f k8s/vacancy-hpa.yaml
	kubectl apply -f k8s/ticket-hpa.yaml
	@echo "$(GREEN)✅ HPAs deployed$(NC)"

.PHONY: hpa-status
hpa-status: ## Show HPA status
	@echo "$(YELLOW)📊 HPA Status:$(NC)"
	@kubectl get hpa -n $(NAMESPACE)
	@echo ""
	@echo "$(YELLOW)📊 Pod Metrics:$(NC)"
	@kubectl top pods -n $(NAMESPACE) 2>/dev/null || echo "$(RED)Metrics not available yet$(NC)"

.PHONY: watch-hpa
watch-hpa: ## Watch HPA scaling in real-time
	@watch -n 2 'kubectl get hpa -n $(NAMESPACE) && echo "" && kubectl get pods -n $(NAMESPACE)'

.PHONY: wait
wait: ## Wait for deployments to be ready
	@echo "$(YELLOW)⏳ Waiting for deployments to be ready...$(NC)"
	kubectl wait --namespace $(NAMESPACE) \
		--for=condition=ready pod \
		--selector=app=vacancy-service \
		--timeout=120s
	kubectl wait --namespace $(NAMESPACE) \
		--for=condition=ready pod \
		--selector=app=ticket-service \
		--timeout=120s
	@echo "$(GREEN)✅ All deployments ready$(NC)"

.PHONY: status
status: ## Show deployment status
	@echo "$(YELLOW)📊 Deployment Status:$(NC)"
	@echo ""
	@echo "$(GREEN)Pods:$(NC)"
	@kubectl get pods -n $(NAMESPACE)
	@echo ""
	@echo "$(GREEN)Services:$(NC)"
	@kubectl get svc -n $(NAMESPACE)
	@echo ""
	@echo "$(GREEN)Ingress:$(NC)"
	@kubectl get ingress -n $(NAMESPACE)

.PHONY: logs
logs: ## Show logs from all services
	@echo "$(YELLOW)📋 Recent logs:$(NC)"
	@echo ""
	@echo "$(GREEN)=== Redis ===$(NC)"
	@kubectl logs -n $(NAMESPACE) -l app=redis --tail=20
	@echo ""
	@echo "$(GREEN)=== Vacancy Service ===$(NC)"
	@kubectl logs -n $(NAMESPACE) -l app=vacancy-service --tail=20
	@echo ""
	@echo "$(GREEN)=== Ticket Service ===$(NC)"
	@kubectl logs -n $(NAMESPACE) -l app=ticket-service --tail=20

.PHONY: logs-redis
logs-redis: ## Show Redis logs
	@kubectl logs -n $(NAMESPACE) -l app=redis -f

.PHONY: logs-vacancy
logs-vacancy: ## Show vacancy service logs
	@kubectl logs -n $(NAMESPACE) -l app=vacancy-service -f

.PHONY: logs-ticket
logs-ticket: ## Show ticket service logs
	@kubectl logs -n $(NAMESPACE) -l app=ticket-service -f

.PHONY: restart
restart: ## Restart all deployments
	@echo "$(YELLOW)🔄 Restarting deployments...$(NC)"
	kubectl rollout restart deployment -n $(NAMESPACE) vacancy-service
	kubectl rollout restart deployment -n $(NAMESPACE) ticket-service
	@echo "$(GREEN)✅ Deployments restarted$(NC)"

.PHONY: scale
scale: ## Scale deployments (usage: make scale REPLICAS=3)
	@echo "$(YELLOW)📈 Scaling deployments to $(REPLICAS) replicas...$(NC)"
	kubectl scale deployment -n $(NAMESPACE) vacancy-service --replicas=$(REPLICAS)
	kubectl scale deployment -n $(NAMESPACE) ticket-service --replicas=$(REPLICAS)
	@echo "$(GREEN)✅ Deployments scaled$(NC)"

.PHONY: test
test: ## Test the deployment
	@echo "$(YELLOW)🧪 Testing deployment...$(NC)"
	@echo ""
	@echo "$(GREEN)1. Redis Connection:$(NC)"
	@kubectl exec -n $(NAMESPACE) deployment/redis -- redis-cli ping
	@echo ""
	@echo "$(GREEN)2. Health Check:$(NC)"
	@curl -s http://ticket.127.0.0.1.nip.io/api/v1/health | jq .
	@echo ""
	@echo "$(GREEN)3. Service Info:$(NC)"
	@curl -s http://ticket.127.0.0.1.nip.io/ | jq .
	@echo ""
	@echo "$(GREEN)3. Purchase Test:$(NC)"
	@curl -s -X POST http://ticket.127.0.0.1.nip.io/api/v1/purchase \
		-H "Content-Type: application/json" \
		-d '{"qty": 1}' | jq .

.PHONY: test-redis
test-redis: ## Test Redis connectivity and data
	@echo "$(YELLOW)🗄️  Testing Redis...$(NC)"
	@echo ""
	@echo "$(GREEN)1. Redis Ping:$(NC)"
	@kubectl exec -n $(NAMESPACE) deployment/redis -- redis-cli ping
	@echo ""
	@echo "$(GREEN)2. Redis Info:$(NC)"
	@kubectl exec -n $(NAMESPACE) deployment/redis -- redis-cli info server | head -10
	@echo ""
	@echo "$(GREEN)3. Redis Keys:$(NC)"
	@kubectl exec -n $(NAMESPACE) deployment/redis -- redis-cli keys "*" | head -10 || echo "No keys found"
	@echo ""

.PHONY: load-test
load-test: ## Run K6 load test
	@echo "$(YELLOW)🔥 Running load test...$(NC)"
	k6 run ticket-system-k6-k8s.js

.PHONY: clean
clean: ## Delete all Kubernetes resources
	@echo "$(YELLOW)🗑️  Deleting Kubernetes resources...$(NC)"
	kubectl delete -f k8s/ingress.yaml --ignore-not-found=true
	kubectl delete -f k8s/ticket-deployment-registry.yaml --ignore-not-found=true
	kubectl delete -f k8s/vacancy-deployment-registry.yaml --ignore-not-found=true
	kubectl delete -f k8s/redis-deployment.yaml --ignore-not-found=true
	kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
	kubectl delete -f k8s/namespace.yaml --ignore-not-found=true
	@echo "$(GREEN)✅ Resources deleted$(NC)"

.PHONY: clean-images
clean-images: ## Remove local Docker images
	@echo "$(YELLOW)🗑️  Removing local images...$(NC)"
	docker rmi vacancy-service:latest || true
	docker rmi ticket-service:latest || true
	docker rmi $(VACANCY_FULL) || true
	docker rmi $(TICKET_FULL) || true
	@echo "$(GREEN)✅ Images removed$(NC)"

.PHONY: registry-images
registry-images: ## List images in registry
	@echo "$(YELLOW)📦 Images in registry:$(NC)"
	@curl -s http://$(REGISTRY)/v2/_catalog | jq .
	@echo ""
	@echo "$(YELLOW)Vacancy service tags:$(NC)"
	@curl -s http://$(REGISTRY)/v2/$(VACANCY_IMAGE)/tags/list | jq .
	@echo ""
	@echo "$(YELLOW)Ticket service tags:$(NC)"
	@curl -s http://$(REGISTRY)/v2/$(TICKET_IMAGE)/tags/list | jq .

.PHONY: describe-pods
describe-pods: ## Describe all pods
	@kubectl describe pods -n $(NAMESPACE)

.PHONY: shell-vacancy
shell-vacancy: ## Open shell in vacancy pod
	@kubectl exec -it -n $(NAMESPACE) deployment/vacancy-service -- /bin/sh

.PHONY: shell-ticket
shell-ticket: ## Open shell in ticket pod
	@kubectl exec -it -n $(NAMESPACE) deployment/ticket-service -- /bin/sh

.PHONY: port-forward-vacancy
port-forward-vacancy: ## Port forward to vacancy service
	@echo "$(GREEN)Port forwarding vacancy service to localhost:8001$(NC)"
	kubectl port-forward -n $(NAMESPACE) svc/vacancy-service 8001:8001

.PHONY: port-forward-ticket
port-forward-ticket: ## Port forward to ticket service
	@echo "$(GREEN)Port forwarding ticket service to localhost:8002$(NC)"
	kubectl port-forward -n $(NAMESPACE) svc/ticket-service 8002:8002

.PHONY: update
update: build push restart wait ## Build, push and update running deployment
	@echo "$(GREEN)✅ Deployment updated successfully!$(NC)"

.PHONY: full-deploy
full-deploy: check-registry build push deploy wait status ## Complete deployment from scratch
	@echo ""
	@echo "$(GREEN)╔══════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║  ✅ Full deployment completed successfully! ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)🌐 Access the application at:$(NC)"
	@echo "   http://ticket.127.0.0.1.nip.io/"
	@echo ""
	@echo "$(YELLOW)📚 View API docs at:$(NC)"
	@echo "   http://ticket.127.0.0.1.nip.io/docs"

.PHONY: dev
dev: update test ## Quick dev cycle: build, push, restart, test
	@echo "$(GREEN)✅ Dev cycle completed!$(NC)"

# Default target
.DEFAULT_GOAL := help
