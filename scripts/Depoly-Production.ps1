# Deploy to production environment
# Optimized for Docker Desktop Kubernetes on Windows
# Usage: .\scripts\Deploy-Production.ps1

param(
    [switch]$SkipBuild = $false,
    [switch]$Force = $false
)

# Error handling
$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying to Production Environment (Docker Desktop)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$NAMESPACE = "production"

# Safety check
if (-not $Force) {
    Write-Host "⚠️  WARNING: You are about to deploy to PRODUCTION!" -ForegroundColor Yellow
    Write-Host ""
    $confirmation = Read-Host "Are you sure you want to continue? (yes/no)"
    
    if ($confirmation -ne "yes") {
        Write-Host "❌ Deployment cancelled" -ForegroundColor Red
        exit 0
    }
    Write-Host ""
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check kubectl
try {
    $null = kubectl version --client 2>&1
    Write-Host "✅ kubectl found" -ForegroundColor Green
} catch {
    Write-Host "❌ kubectl not found" -ForegroundColor Red
    exit 1
}

# Check Docker
try {
    $null = docker --version 2>&1
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verify Docker Desktop Kubernetes
Write-Host "Checking Docker Desktop Kubernetes..." -ForegroundColor Yellow

$context = kubectl config current-context
Write-Host "Current context: $context" -ForegroundColor White

if ($context -ne "docker-desktop") {
    Write-Host "⚠️  Warning: Not using docker-desktop context" -ForegroundColor Yellow
}

Write-Host ""

# Get current git commit
try {
    $gitSha = git rev-parse --short HEAD
    Write-Host "Git commit: $gitSha" -ForegroundColor Cyan
} catch {
    $gitSha = "unknown"
    Write-Host "⚠️  Git commit unknown" -ForegroundColor Yellow
}

Write-Host ""

# Build production images
if (-not $SkipBuild) {
    Write-Host "Building production images with docker-compose..." -ForegroundColor Yellow
    
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

# Tag images for production
Write-Host "Tagging images for production..." -ForegroundColor Yellow

# Tag with git SHA and production label
docker tag ai-forecasting-for-renewable-energy--orchestrator:latest ai-forecasting-for-renewable-energy--orchestrator:production
docker tag ai-forecasting-for-renewable-energy--xgb_service:latest ai-forecasting-for-renewable-energy--xgb_service:production
docker tag ai-forecasting-for-renewable-energy--hw_service:latest ai-forecasting-for-renewable-energy--hw_service:production
docker tag ai-forecasting-for-renewable-energy--gui:latest ai-forecasting-for-renewable-energy--gui:production

docker tag ai-forecasting-for-renewable-energy--orchestrator:latest ai-forecasting-for-renewable-energy--orchestrator:production
docker tag ai-forecasting-for-renewable-energy--xgb_service:latest ai-forecasting-for-renewable-energy--xgb_service:production
docker tag ai-forecasting-for-renewable-energy--hw_service:latest ai-forecasting-for-renewable-energy--hw_service:production
docker tag ai-forecasting-for-renewable-energy--gui:latest ai-forecasting-for-renewable-energy--gui:production
Write-Host "✅ Images tagged" -ForegroundColor Green
Write-Host ""

# Verify images
Write-Host "Verifying images..." -ForegroundColor Yellow
docker images | Select-String "energy"
Write-Host ""

# Create/Update Namespace
Write-Host "Creating/updating namespace..." -ForegroundColor Yellow

kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace $NAMESPACE environment=production --overwrite

Write-Host ""

# Backup current deployment
Write-Host "Backing up current deployment..." -ForegroundColor Yellow

$backupFile = "backup-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss').yaml"

try {
    kubectl get deployment --namespace=$NAMESPACE -o yaml | Out-File -FilePath $backupFile -Encoding UTF8
    Write-Host "✅ Backup saved to: $backupFile" -ForegroundColor Green
} catch {
    Write-Host "⚠️  No existing deployment to backup" -ForegroundColor Yellow
}

Write-Host ""

# Update deployment manifests
Write-Host "Preparing deployment manifests..." -ForegroundColor Yellow

$deploymentContent = Get-Content k8s\deployment.yaml -Raw
$deploymentContent = $deploymentContent -replace ':latest', ':production'
$deploymentContent = $deploymentContent -replace 'imagePullPolicy: Always', 'imagePullPolicy: Never'
$deploymentContent | Out-File -FilePath k8s\deployment-production.yaml -Encoding UTF8

Write-Host "✅ Production manifest created" -ForegroundColor Green
Write-Host ""

# Deploy to Production
Write-Host "Deploying to production..." -ForegroundColor Yellow

kubectl apply -f k8s\deployment-production.yaml --namespace=$NAMESPACE
kubectl apply -f k8s\service.yaml --namespace=$NAMESPACE

# Annotate deployment
kubectl annotate deployment api-deployment `
    kubernetes.io/change-cause="Deployed commit $gitSha by PowerShell script" `
    --namespace=$NAMESPACE --overwrite

Write-Host "✅ Manifests applied" -ForegroundColor Green
Write-Host ""

# Wait for rollout
Write-Host "Waiting for production rollout (this may take several minutes)..." -ForegroundColor Yellow

try {
    kubectl rollout status deployment/api-deployment -n $NAMESPACE --timeout=10m
    if ($LASTEXITCODE -ne 0) { throw }
    
    kubectl rollout status deployment/xgb-deployment -n $NAMESPACE --timeout=10m
    if ($LASTEXITCODE -ne 0) { throw }
    
    kubectl rollout status deployment/hw-deployment -n $NAMESPACE --timeout=10m
    if ($LASTEXITCODE -ne 0) { throw }
    
    kubectl rollout status deployment/gui-deployment -n $NAMESPACE --timeout=10m
    if ($LASTEXITCODE -ne 0) { throw }
    
} catch {
    Write-Host "❌ Deployment failed! Initiating rollback..." -ForegroundColor Red
    Write-Host ""
    
    # Get logs before rollback
    Write-Host "📋 Recent logs:" -ForegroundColor Yellow
    kubectl logs -l app=api-gateway --tail=100 --namespace=$NAMESPACE
    
    # Rollback
    kubectl rollout undo deployment/api-deployment --namespace=$NAMESPACE
    kubectl rollout undo deployment/xgb-deployment --namespace=$NAMESPACE
    kubectl rollout undo deployment/hw-deployment --namespace=$NAMESPACE
    kubectl rollout undo deployment/gui-deployment --namespace=$NAMESPACE
    
    Write-Host "⏪ Rollback completed" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Rollout completed" -ForegroundColor Green
Write-Host ""

# Production Health Checks
Write-Host "Running production health checks..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

$healthCheckPassed = $false

for ($i = 1; $i -le 5; $i++) {
    Write-Host "Health check attempt $i/5..." -ForegroundColor White
    
    try {
        kubectl run prod-health-check-$i `
            --image=curlimages/curl `
            --rm -i --restart=Never `
            --namespace=$NAMESPACE `
            -- curl -f http://api-service:8000/health 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Health check passed on attempt $i" -ForegroundColor Green
            $healthCheckPassed = $true
            break
        }
    } catch {
        Write-Host "❌ Health check failed on attempt $i" -ForegroundColor Red
    }
    
    if ($i -lt 5) {
        Start-Sleep -Seconds 10
    }
}

if (-not $healthCheckPassed) {
    Write-Host "❌ All health checks failed!" -ForegroundColor Red
    Write-Host "Rolling back deployment..." -ForegroundColor Yellow
    
    kubectl rollout undo deployment/api-deployment --namespace=$NAMESPACE
    exit 1
}

Write-Host ""

# Verify Deployment Success
Write-Host "✅ Production deployment successful!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Deployment Status:" -ForegroundColor Cyan
kubectl get deployments --namespace=$NAMESPACE
Write-Host ""
Write-Host "🎯 Pod Status:" -ForegroundColor Cyan
kubectl get pods --namespace=$NAMESPACE
Write-Host ""
Write-Host "🌐 Services:" -ForegroundColor Cyan
kubectl get services --namespace=$NAMESPACE
Write-Host ""
Write-Host "📍 Access URLs (Docker Desktop):" -ForegroundColor Cyan
Write-Host "   GUI: http://localhost:30001" -ForegroundColor White
Write-Host "   API: http://localhost:30000" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Revision History:" -ForegroundColor Cyan
kubectl rollout history deployment/api-deployment --namespace=$NAMESPACE

Write-Host ""

# Cleanup temp files
if (Test-Path k8s\deployment-production.yaml) {
    Remove-Item k8s\deployment-production.yaml -Force
}

Write-Host "🎉 Production deployment complete!" -ForegroundColor Green