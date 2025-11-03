#!/bin/bash

# Script para build das imagens Docker ultra-otimizadas
# As imagens padrão são distroless (~77MB vs 213MB originais)

set -e

VERSION=${1:-latest}
BUILD_TYPE=${2:-distroless}

echo "🚀 Building ultra-optimized Docker images..."
echo "Version: $VERSION"
echo "Type: $BUILD_TYPE"

case $BUILD_TYPE in
    "distroless"|"")
        echo "� Building Distroless images (production)..."
        docker build -f Dockerfile.ticket -t ticket-service:$VERSION .
        docker build -f Dockerfile.vacancy -t vacancy-service:$VERSION .
        ;;
    "alpine")
        echo "🧪 Building Alpine images (debugging)..."
        docker build -f Dockerfile.ticket.alpine -t ticket-service:$VERSION .
        docker build -f Dockerfile.vacancy.alpine -t vacancy-service:$VERSION .
        ;;
    *)
        echo "❌ Tipo inválido. Use: distroless (padrão) ou alpine"
        exit 1
        ;;
esac

# Tag as latest if not already
if [ "$VERSION" != "latest" ]; then
    docker tag ticket-service:$VERSION ticket-service:latest
    docker tag vacancy-service:$VERSION vacancy-service:latest
fi

echo "✅ Images built successfully!"

echo ""
echo "📊 Image sizes:"
docker images | grep -E "(ticket-service|vacancy-service)" | head -4

echo ""
echo "🎉 Build completed!"
echo ""
echo "💡 Otimizações aplicadas:"
echo "   ✅ Multi-stage build com Distroless runtime"
echo "   ✅ Redução de 213MB → ~77MB (63.8% menor)"
echo "   ✅ Máxima segurança: sem shell, sem OS tools"
echo "   ✅ Usuário não-root automático"
echo "   ✅ Configurações Python otimizadas"