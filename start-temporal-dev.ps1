# Start Temporal Development Environment
# This script starts all Temporal services for local development

Write-Host "Starting Temporal Development Environment..." -ForegroundColor Green

# Check if Docker is running
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please update .env with your configuration and run this script again." -ForegroundColor Yellow
    exit 1
}

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

Write-Host "`nStep 1: Starting PostgreSQL and Redis..." -ForegroundColor Cyan
docker-compose up -d postgres redis

Write-Host "`nWaiting for PostgreSQL to be ready..."
Start-Sleep -Seconds 5

Write-Host "`nStep 2: Starting Temporal Server..." -ForegroundColor Cyan
docker-compose up -d temporal

Write-Host "`nWaiting for Temporal Server to be ready..."
Start-Sleep -Seconds 10

Write-Host "`nStep 3: Starting Temporal UI..." -ForegroundColor Cyan
docker-compose up -d temporal-ui

Write-Host "`nStep 4: Starting Temporal Worker..." -ForegroundColor Cyan
docker-compose up -d temporal-worker

Write-Host "`nStep 5: Starting Backend API..." -ForegroundColor Cyan
docker-compose up -d backend

Write-Host "`n✅ Temporal Development Environment Started!" -ForegroundColor Green

Write-Host "`nServices Status:" -ForegroundColor Yellow
docker-compose ps

Write-Host "`nAccess Points:" -ForegroundColor Yellow
Write-Host "  📊 Temporal UI:    http://localhost:8080" -ForegroundColor White
Write-Host "  🚀 Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "  📝 API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "  🗄️  PostgreSQL:     localhost:5432" -ForegroundColor White
Write-Host "  🔴 Redis:          localhost:6379" -ForegroundColor White

Write-Host "`nUseful Commands:" -ForegroundColor Yellow
Write-Host "  View logs:         docker-compose logs -f [service]" -ForegroundColor White
Write-Host "  Stop all:          docker-compose down" -ForegroundColor White
Write-Host "  Restart worker:    docker-compose restart temporal-worker" -ForegroundColor White
Write-Host "  View worker logs:  docker-compose logs -f temporal-worker" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Open Temporal UI: http://localhost:8080" -ForegroundColor White
Write-Host "  2. Submit a test task via API" -ForegroundColor White
Write-Host "  3. Watch workflow execution in Temporal UI" -ForegroundColor White

Write-Host "`nPress Ctrl+C to view logs (or run: docker-compose logs -f)" -ForegroundColor Cyan
