# Automated Local Installation Script for Windows (PowerShell)
# Run with: .\setup.ps1

Write-Host "=== Employee Compensation Service Setup ===" -ForegroundColor Cyan

# 1. Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3.9+ is required but was not found in PATH. Please install Python and try again."
    exit 1
}

# 2. Check / Create Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "Virtual environment (.venv) already exists." -ForegroundColor Green
}

# 3. Activate Virtual Environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# 4. Install Dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Create local.settings.json if missing
if (-not (Test-Path "local.settings.json")) {
    if (Test-Path "local.settings.example.json") {
        Write-Host "Creating local.settings.json from local.settings.example.json..." -ForegroundColor Yellow
        Copy-Item "local.settings.example.json" "local.settings.json"
        Write-Host "Created local.settings.json. Please verify connection credentials in it." -ForegroundColor Green
    }
} else {
    Write-Host "local.settings.json already exists." -ForegroundColor Green
}

# 6. Check Azure Functions Core Tools
if (-not (Get-Command func -ErrorAction SilentlyContinue)) {
    Write-Host "[WARNING] Azure Functions Core Tools ('func') not found in PATH." -ForegroundColor Yellow
    Write-Host "Install via winget: winget install Microsoft.Azure.FunctionsCoreTools --accept-package-agreements --accept-source-agreements" -ForegroundColor Yellow
} else {
    Write-Host "Azure Functions Core Tools detected: $(func --version)" -ForegroundColor Green
}

Write-Host "`n=== Installation Complete! ===" -ForegroundColor Cyan
Write-Host "Next steps for execution:"
Write-Host "1. Start SQL Server (e.g. docker run or local service)"
Write-Host "2. Run database migrations: python run_migrations.py"
Write-Host "3. Start the function app: func start (or .\start.ps1)"
