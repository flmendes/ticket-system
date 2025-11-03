#!/bin/bash
# Install metrics-server for Kubernetes HPA support
# Configured for kind clusters

set -e

echo "🔧 Installing metrics-server for Kubernetes..."
echo ""

# Install metrics-server
echo "📦 Applying metrics-server manifest..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

echo ""
echo "⏳ Waiting for deployment to be created..."
sleep 5

# Patch for kind (insecure TLS)
echo "🔧 Patching metrics-server for kind cluster..."
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo ""
echo "⏳ Waiting for metrics-server to be ready..."
kubectl wait --for=condition=ready pod -l k8s-app=metrics-server -n kube-system --timeout=90s || true

echo ""
echo "🧪 Testing metrics-server..."
sleep 10

# Test metrics
echo "📊 Node metrics:"
kubectl top nodes || echo "⚠️  Metrics not ready yet, may need 30-60 more seconds"

echo ""
echo "✅ Metrics-server installation complete!"
echo ""
echo "To verify metrics are working:"
echo "  kubectl top nodes"
echo "  kubectl top pods -n ticket-system"
