#!/bin/bash
# Elder Flow Deployment Script
# Deploy Elder Flow to Kubernetes cluster

set -e

NAMESPACE="elder-flow"
REGISTRY="elderflow"
VERSION=${1:-latest}

echo "🌊🧙‍♂️ Elder Flow Kubernetes Deployment Script"
echo "============================================"
echo "Version: $VERSION"
echo "Namespace: $NAMESPACE"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required but not installed. Aborting." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ docker is required but not installed. Aborting." >&2; exit 1; }

# Check kubectl connection
echo "Checking Kubernetes cluster connection..."
kubectl cluster-info || { echo "❌ Cannot connect to Kubernetes cluster. Please configure kubectl." >&2; exit 1; }

# Create namespace
echo ""
echo "Creating namespace..."
kubectl apply -f kubernetes/namespace.yaml

# Create secrets (if not exists)
echo ""
echo "Checking secrets..."
if ! kubectl get secret elder-flow-secrets -n $NAMESPACE >/dev/null 2>&1; then
    echo "⚠️  Secrets not found. Please create them:"
    echo "   1. Copy kubernetes/secrets.yaml to kubernetes/secrets-prod.yaml"
    echo "   2. Update all placeholder values with actual secrets"
    echo "   3. Run: kubectl apply -f kubernetes/secrets-prod.yaml"
    echo ""
    read -p "Have you created the secrets? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled. Please create secrets first."
        exit 1
    fi
fi

# Build and push Docker images
echo ""
echo "Building Docker images..."
docker build -t $REGISTRY/elder-flow:$VERSION -f docker/Dockerfile.elder-flow .

echo ""
read -p "Push images to registry? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push $REGISTRY/elder-flow:$VERSION
fi

# Deploy ConfigMaps
echo ""
echo "Deploying ConfigMaps..."
kubectl apply -f kubernetes/configmap.yaml

# Deploy databases
echo ""
echo "Deploying databases..."
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/redis-deployment.yaml

# Wait for databases to be ready
echo ""
echo "Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l component=database -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l component=cache -n $NAMESPACE --timeout=300s

# Deploy Elder Flow core
echo ""
echo "Deploying Elder Flow API..."
kubectl apply -f kubernetes/elderflow-deployment.yaml

# Deploy workers
echo ""
echo "Deploying workers..."
kubectl apply -f kubernetes/workers-deployment.yaml

# Deploy monitoring
echo ""
echo "Deploying monitoring stack..."
kubectl apply -f kubernetes/monitoring.yaml

# Deploy ingress
echo ""
echo "Deploying ingress..."
kubectl apply -f kubernetes/ingress.yaml

# Apply network policies
echo ""
echo "Applying network policies..."
kubectl apply -f kubernetes/network-policies.yaml

# Wait for deployments
echo ""
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available deployment --all -n $NAMESPACE --timeout=600s

# Show status
echo ""
echo "Deployment complete! 🎉"
echo ""
echo "Elder Flow Status:"
kubectl get pods -n $NAMESPACE
echo ""
echo "Services:"
kubectl get services -n $NAMESPACE
echo ""
echo "Ingress:"
kubectl get ingress -n $NAMESPACE

# Get ingress IP/hostname
INGRESS_HOST=$(kubectl get ingress elder-flow-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
if [ -z "$INGRESS_HOST" ]; then
    INGRESS_HOST=$(kubectl get ingress elder-flow-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
fi

echo ""
echo "🌊 Elder Flow is deployed!"
echo "========================="
echo "Main URL: https://elderflow.ai (or https://$INGRESS_HOST)"
echo "API URL: https://api.elderflow.ai (or https://$INGRESS_HOST/api)"
echo "Admin URL: https://admin.elderflow.ai"
echo "Grafana: https://$INGRESS_HOST:3000"
echo ""
echo "Next steps:"
echo "1. Update DNS records to point to: $INGRESS_HOST"
echo "2. Access Grafana to view metrics"
echo "3. Check logs: kubectl logs -f deployment/elder-flow-api -n $NAMESPACE"
echo ""
echo "🧙‍♂️ Think it, Rule it, Own it! 🧙‍♂️"
