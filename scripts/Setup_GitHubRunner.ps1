# Setup GitHub Actions self-hosted runner on Windows
# This allows GitHub Actions to deploy to your local Kubernetes cluster
# Usage: .\scripts\Setup-GitHubRunner.ps1

param(
    [string]$RepoUrl = "https://github.com/Apurba1001/AI-Forecasting-for-Renewable-Energy-",
    [string]$RunnerToken = "AUFU6EGULGSWRSES2OUPOXLJLOQLG"
)

# Error handling
$ErrorActionPreference = "Stop"

Write-Host "🤖 GitHub Actions Self-Hosted Runner Setup (Windows)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Get GitHub repository information
if ([string]::IsNullOrEmpty($RepoUrl)) {
    Write-Host "📝 GitHub Repository Information" -ForegroundColor Yellow
    Write-Host "   Format: https://github.com/OWNER/REPO" -ForegroundColor White
    Write-Host ""
    $RepoUrl = Read-Host "Enter your GitHub repository URL"
}

# Extract owner and repo
if ($RepoUrl -match 'github\.com/([^/]+)/(.+?)(?:\.git)?$') {
    $RepoOwner = $Matches[1]
    $RepoName = $Matches[2]
} else {
    Write-Host "❌ Invalid repository URL format" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Repository: $RepoOwner/$RepoName" -ForegroundColor Green
Write-Host ""

# Get runner token
if ([string]::IsNullOrEmpty($RunnerToken)) {
    Write-Host "🔑 Getting runner token..." -ForegroundColor Yellow
    Write-Host "   1. Go to: https://github.com/$RepoOwner/$RepoName/settings/actions/runners/new" -ForegroundColor White
    Write-Host "   2. Click 'New self-hosted runner'" -ForegroundColor White
    Write-Host "   3. Select 'Windows'" -ForegroundColor White
    Write-Host "   4. Copy the token from the 'Configure' section" -ForegroundColor White
    Write-Host ""
    $RunnerToken = Read-Host "Paste your runner token"
}

Write-Host ""

# Create runner directory
$RunnerDir = "$HOME\actions-runner"
Write-Host "Creating runner directory: $RunnerDir" -ForegroundColor Yellow

if (Test-Path $RunnerDir) {
    Write-Host "⚠️  Directory already exists. Removing..." -ForegroundColor Yellow
    Remove-Item $RunnerDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $RunnerDir | Out-Null
Set-Location $RunnerDir

Write-Host "✅ Directory created" -ForegroundColor Green
Write-Host ""

# Download latest runner
Write-Host "Downloading GitHub Actions runner..." -ForegroundColor Yellow

$RunnerVersion = "2.311.0"
$RunnerFile = "actions-runner-win-x64-$RunnerVersion.zip"
$DownloadUrl = "https://github.com/actions/runner/releases/download/v$RunnerVersion/$RunnerFile"

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $RunnerFile
    Write-Host "✅ Download complete" -ForegroundColor Green
} catch {
    Write-Host "❌ Download failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Extract runner
Write-Host "Extracting runner..." -ForegroundColor Yellow

try {
    Expand-Archive -Path $RunnerFile -DestinationPath . -Force
    Remove-Item $RunnerFile -Force
    Write-Host "✅ Extraction complete" -ForegroundColor Green
} catch {
    Write-Host "❌ Extraction failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Configure runner
Write-Host "Configuring runner..." -ForegroundColor Yellow
Write-Host ""

try {
    & .\config.cmd `
        --url "https://github.com/$RepoOwner/$RepoName" `
        --token $RunnerToken `
        --name "windows-k8s-runner" `
        --work "_work" `
        --labels "self-hosted,Windows,kubernetes" `
        --unattended
    
    if ($LASTEXITCODE -ne 0) {
        throw "Configuration failed"
    }
    
} catch {
    Write-Host "❌ Configuration failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Runner configured" -ForegroundColor Green
Write-Host ""

# Install as Windows service
Write-Host "Installing runner as Windows service..." -ForegroundColor Yellow
Write-Host "   (This requires Administrator privileges)" -ForegroundColor White
Write-Host ""

try {
    # Check if running as administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-Host "⚠️  Not running as Administrator" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To install as a service, run this script as Administrator:" -ForegroundColor Yellow
        Write-Host "   1. Right-click PowerShell" -ForegroundColor White
        Write-Host "   2. Select 'Run as Administrator'" -ForegroundColor White
        Write-Host "   3. Run: .\svc.sh install" -ForegroundColor White
        Write-Host ""
        Write-Host "Or run manually (no service):" -ForegroundColor Yellow
        Write-Host "   cd $RunnerDir" -ForegroundColor White
        Write-Host "   .\run.cmd" -ForegroundColor White
    } else {
        # Install service
        & .\svc.sh install
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Service installed" -ForegroundColor Green
            Write-Host ""
            
            # Start service
            Write-Host "Starting service..." -ForegroundColor Yellow
            & .\svc.sh start
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Service started" -ForegroundColor Green
                Write-Host ""
                Write-Host "Service commands:" -ForegroundColor Cyan
                Write-Host "   Status:  .\svc.sh status" -ForegroundColor White
                Write-Host "   Stop:    .\svc.sh stop" -ForegroundColor White
                Write-Host "   Start:   .\svc.sh start" -ForegroundColor White
            }
        }
    }
} catch {
    Write-Host "⚠️  Service installation failed: $_" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can still run the runner manually:" -ForegroundColor Yellow
    Write-Host "   cd $RunnerDir" -ForegroundColor White
    Write-Host "   .\run.cmd" -ForegroundColor White
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Verify runner is online: https://github.com/$RepoOwner/$RepoName/settings/actions/runners" -ForegroundColor White
Write-Host "   2. Push to 'main' branch to trigger staging deployment" -ForegroundColor White
Write-Host "   3. Merge to 'main' branch to trigger production deployment" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: If service didn't install, run this script as Administrator or use:" -ForegroundColor Yellow
Write-Host "   cd $RunnerDir" -ForegroundColor White
Write-Host "   .\run.cmd" -ForegroundColor White
Write-Host ""