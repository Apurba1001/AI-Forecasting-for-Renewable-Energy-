# build-all.ps1
Write-Host "🏗️  Building all Docker images..." -ForegroundColor Cyan

docker build --no-cache -t energy-api:latest -f Dockerfile.api .
docker build --no-cache -t energy-xgb:latest -f Dockerfile.xgb .
docker build --no-cache -t energy-hw:latest -f Dockerfile.hw .
docker build --no-cache -t energy-gui:latest -f Dockerfile.gui .
Write-Host "✅  All Docker images built successfully!" -ForegroundColor Green