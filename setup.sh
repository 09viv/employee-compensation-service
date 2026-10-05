#!/usr/bin/env bash
# Automated Local Installation Script for Linux/macOS (Bash)
# Run with: chmod +x setup.sh && ./setup.sh

set -e

echo "=== Employee Compensation Service Setup ==="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

# 2. Check / Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "Virtual environment (.venv) already exists."
fi

# 3. Activate Virtual Environment
echo "Activating virtual environment..."
source .venv/bin/activate

# 4. Install Dependencies
echo "Installing dependencies from requirements.txt..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Create local.settings.json if missing
if [ ! -f "local.settings.json" ]; then
    if [ -f "local.settings.example.json" ]; then
        echo "Creating local.settings.json from local.settings.example.json..."
        cp local.settings.example.json local.settings.json
        echo "Created local.settings.json. Please verify connection credentials in it."
    fi
else
    echo "local.settings.json already exists."
fi

# 6. Check Azure Functions Core Tools
if ! command -v func &> /dev/null; then
    echo "[WARNING] Azure Functions Core Tools ('func') not found in PATH."
else
    echo "Azure Functions Core Tools detected: $(func --version)"
fi

echo ""
echo "=== Installation Complete! ==="
echo "Next steps for execution:"
echo "1. Start SQL Server (e.g., docker run or Azure SQL)"
echo "2. Run database migrations: python run_migrations.py"
echo "3. Start the function app: func start (or ./start.sh)"
