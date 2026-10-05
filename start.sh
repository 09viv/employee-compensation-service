#!/usr/bin/env bash
# Local Execution Script for Linux/macOS (Bash)
# Run with: chmod +x start.sh && ./start.sh

set -e

echo "=== Starting Employee Compensation Service ==="

# 1. Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

# 2. Check local.settings.json
if [ ! -f "local.settings.json" ]; then
    echo "Error: local.settings.json is missing! Run ./setup.sh or copy local.settings.example.json first."
    exit 1
fi

# 3. Check func
if ! command -v func &> /dev/null; then
    echo "Error: Azure Functions Core Tools ('func') not found in PATH."
    exit 1
fi

# 4. Start host
echo "Starting Azure Functions host on http://localhost:7071 ..."
func start
