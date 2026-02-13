#!/usr/bin/env bash
# =============================================================================
# OSS License Generation Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_DIR/docs/docs/legal"

mkdir -p "$OUTPUT_DIR"

echo "=== Generating OSS License Reports ==="

# Frontend (npm)
echo "Scanning frontend dependencies..."
cd "$PROJECT_DIR/frontend"
if [ -f node_modules/.package-lock.json ]; then
    npx license-checker --json --out "$OUTPUT_DIR/frontend-licenses.json" 2>/dev/null || true
    npx license-checker --csv --out "$OUTPUT_DIR/frontend-licenses.csv" 2>/dev/null || true
    echo "✓ Frontend licenses generated"
else
    echo "⚠ Frontend node_modules not found. Run 'npm install' first."
fi

# Backend (pip)
echo "Scanning backend dependencies..."
cd "$PROJECT_DIR/backend"
if [ -d .venv ]; then
    source .venv/bin/activate
    pip-licenses --format=json --output-file="$OUTPUT_DIR/backend-licenses.json" 2>/dev/null || true
    pip-licenses --format=csv --output-file="$OUTPUT_DIR/backend-licenses.csv" 2>/dev/null || true
    deactivate
    echo "✓ Backend licenses generated"
else
    echo "⚠ Backend venv not found. Run 'python -m venv .venv && pip install -e .[dev]' first."
fi

# Gateway (Go)
echo "Scanning gateway dependencies..."
cd "$PROJECT_DIR/gateway"
if command -v go-licenses &> /dev/null; then
    go-licenses csv ./... > "$OUTPUT_DIR/gateway-licenses.csv" 2>/dev/null || true
    echo "✓ Gateway licenses generated"
else
    echo "⚠ go-licenses not found. Install: go install github.com/google/go-licenses@latest"
fi

echo ""
echo "=== License reports generated in $OUTPUT_DIR ==="
