# Deploy to local staging environment
# Optimized for Docker Desktop Kubernetes on Windows
# Usage: .\scripts\Deploy-Staging.ps1

param(
    [switch]$SkipBuild = $false
)

# Error handling
$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying to Staging Environment (Docker Desktop)" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$NAMESPACE = "staging"

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check kubectl
try {
    $null = kubectl version --client 2>&1
    Write-Host "✅ kubectl found" -ForegroundColor Green
} catch {
    Write-Host "❌ kubectl not found. Install via: winget install Kubernetes.kubectl" -ForegroundColor Red
    exit 1
}

# Check Docker
try {
    $null = docker --version 2>&1
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check docker-compose
try {
    $null = docker-compose --version 2>&1
    Write-Host "✅ docker-compose found" -ForegroundColor Green
} catch {
    Write-Host "❌ docker-compose not found. Install Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verify Docker Desktop Kubernetes
Write-Host "Checking Docker Desktop Kubernetes..." -ForegroundColor Yellow

$context = kubectl config current-context
if ($context -ne "docker-desktop") {
    Write-Host "❌ Not using docker-desktop context. Current: $context" -ForegroundColor Red
    Write-Host "Enable Kubernetes in Docker Desktop: Settings → Kubernetes → Enable" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Docker Desktop Kubernetes is running" -ForegroundColor Green
Write-Host ""

# Build images using docker-compose
if (-not $SkipBuild) {
    Write-Host "Building images with docker-compose..." -ForegroundColor Yellow
    
    docker-compose build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Build failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Images built successfully" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⏭️  Skipping build (using existing images)" -ForegroundColor Yellow
    Write-Host ""
}

# Tag images for staging
Write-Host "Tagging images for staging..." -ForegroundColor Yellow

docker tag ai-forecasting-for-renewable-energy--orchestrator:latest ai-forecasting-for-renewable-energy--orchestrator:staging
docker tag ai-forecasting-for-renewable-energy--xgb_service:latest ai-forecasting-for-renewable-energy--xgb_service:staging
docker tag ai-forecasting-for-renewable-energy--hw_service:latest ai-forecasting-for-renewable-energy--hw_service:staging
docker tag ai-forecasting-for-renewable-energy--gui:latest ai-forecasting-for-renewable-energy--gui:staging


Write-Host "✅ Images tagged" -ForegroundColor Green
Write-Host ""

# Images are automatically available in Docker Desktop Kubernetes
Write-Host "✅ Images available to Kubernetes (Docker Desktop)" -ForegroundColor Green
Write-Host ""

# Create namespace
Write-Host "Creating/updating namespace..." -ForegroundColor Yellow

kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace $NAMESPACE environment=staging --overwrite

Write-Host ""

# Deploy to Kubernetes
Write-Host "Deploying to Kubernetes..." -ForegroundColor Yellow

# Update deployment to use staging tags and imagePullPolicy: Never
$deploymentContent = Get-Content k8s\k8s-deployment.yaml -Raw
$deploymentContent = $deploymentContent -replace ':latest', ':staging'
$deploymentContent = $deploymentContent -replace 'imagePullPolicy: Always', 'imagePullPolicy: Never'
$deploymentContent | Out-File -FilePath k8s\k8s-deployment-staging.yaml -Encoding UTF8

kubectl apply -f k8s\k8s-deployment-staging.yaml -n $NAMESPACE
kubectl apply -f k8s\service.yaml -n $NAMESPACE

Write-Host "✅ Manifests applied" -ForegroundColor Green
Write-Host ""

# Wait for rollout
Write-Host "Waiting for rollout to complete..." -ForegroundColor Yellow

try {
    kubectl rollout status deployment/api-deployment -n $NAMESPACE --timeout=5m
    if ($LASTEXITCODE -ne 0) { throw }
    
    kubectl rollout status deployment/xgb-deployment -n $NAMESPACE --timeout=5m
    if ($LASTEXITCODE -ne 0) { throw }
    
    kubectl rollout status deployment/hw-deployment -n $NAMESPACE --timeout=5m
    if ($LASTEXITCODE -ne 0) { throw }
    
    kubectl rollout status deployment/gui-deployment -n $NAMESPACE --timeout=5m
    if ($LASTEXITCODE -ne 0) { throw }
    
} catch {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pod status:" -ForegroundColor Yellow
    kubectl get pods -n $NAMESPACE
    Write-Host ""
    Write-Host "Recent logs:" -ForegroundColor Yellow
    kubectl logs -l app=api-gateway --tail=50 -n $NAMESPACE
    exit 1
}

Write-Host "✅ Rollout completed" -ForegroundColor Green
Write-Host ""

# Verify deployment
Write-Host "Verifying deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

kubectl get pods -n $NAMESPACE
Write-Host ""
kubectl get services -n $NAMESPACE

Write-Host ""
Write-Host "✅ Staging deployment successful!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access URLs (Docker Desktop):" -ForegroundColor Cyan
Write-Host "   GUI: http://localhost:30001" -ForegroundColor White
Write-Host "   API: http://localhost:30000" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs:    kubectl logs -f deployment/api-deployment -n $NAMESPACE" -ForegroundColor White
Write-Host "   View pods:    kubectl get pods -n $NAMESPACE" -ForegroundColor White
Write-Host "   Port forward: kubectl port-forward svc/gui-service 8501:8501 -n $NAMESPACE" -ForegroundColor White
Write-Host "   Delete env:   kubectl delete namespace $NAMESPACE" -ForegroundColor White
Write-Host ""

# Cleanup temp file
if (Test-Path k8s\deployment-staging.yaml) {
    Remove-Item k8s\deployment-staging.yaml -Force
}

Write-Host "🎉 Done!" -ForegroundColor Green