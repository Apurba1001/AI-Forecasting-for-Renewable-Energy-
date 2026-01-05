# Kubernetes Utility Functions for Renewable Energy Forecast System
# Usage: .\scripts\K8s-Utils.ps1 -Command <command> [options]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('status', 'logs', 'restart', 'delete', 'port-forward', 'describe', 'shell')]
    [string]$Command,
    
    [ValidateSet('staging', 'production', 'all')]
    [string]$Namespace = 'staging',
    
    [string]$Pod = "",
    
    [string]$Deployment = "api-deployment",
    
    [int]$Port = 8501,
    
    [int]$Lines = 50
)

$ErrorActionPreference = "Stop"

# Helper function to get namespaces
function Get-Namespaces {
    if ($Namespace -eq 'all') {
        return @('staging', 'production')
    }
    return @($Namespace)
}

# Status command
function Show-Status {
    $namespaces = Get-Namespaces
    
    foreach ($ns in $namespaces) {
        Write-Host ""
        Write-Host "📊 Status for namespace: $ns" -ForegroundColor Cyan
        Write-Host "================================" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "Deployments:" -ForegroundColor Yellow
        kubectl get deployments -n $ns
        Write-Host ""
        
        Write-Host "Pods:" -ForegroundColor Yellow
        kubectl get pods -n $ns -o wide
        Write-Host ""
        
        Write-Host "Services:" -ForegroundColor Yellow
        kubectl get services -n $ns
        Write-Host ""
    }
}

# Logs command
function Show-Logs {
    param([string]$ns)
    
    Write-Host "📋 Logs for $Deployment in $ns" -ForegroundColor Cyan
    Write-Host ""
    
    if ([string]::IsNullOrEmpty($Pod)) {
        # Follow logs from deployment
        Write-Host "Following logs (Ctrl+C to stop)..." -ForegroundColor Yellow
        kubectl logs -f deployment/$Deployment -n $ns --tail=$Lines
    } else {
        # Show logs from specific pod
        Write-Host "Logs from pod: $Pod" -ForegroundColor Yellow
        kubectl logs $Pod -n $ns --tail=$Lines
    }
}

# Restart command
function Restart-Deployment {
    param([string]$ns)
    
    Write-Host "🔄 Restarting $Deployment in $ns..." -ForegroundColor Yellow
    kubectl rollout restart deployment/$Deployment -n $ns
    
    Write-Host ""
    Write-Host "Waiting for rollout..." -ForegroundColor Yellow
    kubectl rollout status deployment/$Deployment -n $ns
    
    Write-Host ""
    Write-Host "✅ Restart complete" -ForegroundColor Green
}

# Delete command
function Remove-Environment {
    param([string]$ns)
    
    Write-Host "⚠️  WARNING: This will delete all resources in namespace '$ns'" -ForegroundColor Yellow
    $confirmation = Read-Host "Are you sure? (yes/no)"
    
    if ($confirmation -eq 'yes') {
        Write-Host "Deleting namespace $ns..." -ForegroundColor Red
        kubectl delete namespace $ns
        Write-Host "✅ Namespace deleted" -ForegroundColor Green
    } else {
        Write-Host "❌ Cancelled" -ForegroundColor Yellow
    }
}

# Port-forward command
function Start-PortForward {
    param([string]$ns)
    
    Write-Host "🔌 Port forwarding GUI service in $ns" -ForegroundColor Cyan
    Write-Host "   Local: http://localhost:$Port" -ForegroundColor White
    Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    kubectl port-forward -n $ns svc/gui-service "$($Port):8501"
}

# Describe command
function Show-Description {
    param([string]$ns)
    
    if ([string]::IsNullOrEmpty($Pod)) {
        # List pods first
        Write-Host "Pods in $ns:" -ForegroundColor Yellow
        kubectl get pods -n $ns
        Write-Host ""
        
        $podName = Read-Host "Enter pod name to describe"
        $Pod = $podName
    }
    
    Write-Host ""
    Write-Host "📝 Describing pod: $Pod" -ForegroundColor Cyan
    Write-Host ""
    
    kubectl describe pod $Pod -n $ns
}

# Shell command
function Start-Shell {
    param([string]$ns)
    
    if ([string]::IsNullOrEmpty($Pod)) {
        # List pods first
        Write-Host "Pods in $ns:" -ForegroundColor Yellow
        kubectl get pods -n $ns
        Write-Host ""
        
        $podName = Read-Host "Enter pod name for shell access"
        $Pod = $podName
    }
    
    Write-Host ""
    Write-Host "🐚 Starting shell in pod: $Pod" -ForegroundColor Cyan
    Write-Host "   Type 'exit' to quit" -ForegroundColor Yellow
    Write-Host ""
    
    kubectl exec -it $Pod -n $ns -- /bin/sh
}

# Main execution
try {
    switch ($Command) {
        'status' {
            Show-Status
        }
        'logs' {
            $namespaces = Get-Namespaces
            foreach ($ns in $namespaces) {
                Show-Logs -ns $ns
            }
        }
        'restart' {
            $namespaces = Get-Namespaces
            foreach ($ns in $namespaces) {
                Restart-Deployment -ns $ns
            }
        }
        'delete' {
            $namespaces = Get-Namespaces
            foreach ($ns in $namespaces) {
                Remove-Environment -ns $ns
            }
        }
        'port-forward' {
            Start-PortForward -ns $Namespace
        }
        'describe' {
            Show-Description -ns $Namespace
        }
        'shell' {
            Start-Shell -ns $Namespace
        }
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}