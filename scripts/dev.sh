#!/usr/bin/env bash
# =============================================================================
# Dev Script - Start development environment
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== Starting Development Environment ==="

# Run setup if .env doesn't exist
if [ ! -f .env ]; then
    echo "Running initial setup..."
    "$SCRIPT_DIR/setup.sh"
fi

# Build and start
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

echo ""
echo "=== Services Started ==="
echo "  Frontend:  http://localhost:5173 (dev) / http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  Swagger:   http://localhost:8000/docs"
echo "  Gateway:   ws://localhost:8080/ws"
echo ""
echo "Logs: docker compose logs -f"
echo "Stop: docker compose down"
