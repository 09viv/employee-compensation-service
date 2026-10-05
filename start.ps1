# Local Execution Script for Windows (PowerShell)
# Run with: .\start.ps1

Write-Host "=== Starting Employee Compensation Service ===" -ForegroundColor Cyan

# 1. Activate venv if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment (.venv)..." -ForegroundColor Yellow
    & ".\.venv\Scripts\Activate.ps1"
}

# 2. Check if local.settings.json exists
if (-not (Test-Path "local.settings.json")) {
    Write-Error "local.settings.json is missing! Run .\setup.ps1 or copy local.settings.example.json first."
    exit 1
}

# 3. Check func
if (-not (Get-Command func -ErrorAction SilentlyContinue)) {
    Write-Error "Azure Functions Core Tools ('func') not found in PATH. Please install it first."
    exit 1
}

# 4. Start host
Write-Host "Starting Azure Functions host on http://localhost:7071 ..." -ForegroundColor Green
func start
