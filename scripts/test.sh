#!/usr/bin/env bash
# =============================================================================
# Test Script - Run tests for all or specific services
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

SERVICE="${1:-all}"

run_frontend_tests() {
    echo "=== Frontend Tests ==="
    cd "$PROJECT_DIR/frontend"
    if [ -f node_modules/.package-lock.json ]; then
        npx vitest run --coverage
    else
        docker compose exec frontend npm run test -- --coverage
    fi
    echo "✓ Frontend tests passed"
}

run_backend_tests() {
    echo "=== Backend Tests ==="
    cd "$PROJECT_DIR/backend"
    if [ -d .venv ]; then
        source .venv/bin/activate
        pytest --cov=app --cov-report=html --cov-report=term-missing -v
    else
        docker compose exec backend pytest --cov=app --cov-report=term-missing -v
    fi
    echo "✓ Backend tests passed"
}

run_gateway_tests() {
    echo "=== Gateway Tests ==="
    cd "$PROJECT_DIR/gateway"
    if command -v go &> /dev/null; then
        go test ./... -v -race -coverprofile=coverage.out
        go tool cover -func=coverage.out
    else
        docker compose exec gateway go test ./... -v -race
    fi
    echo "✓ Gateway tests passed"
}

case "$SERVICE" in
    frontend)
        run_frontend_tests
        ;;
    backend)
        run_backend_tests
        ;;
    gateway)
        run_gateway_tests
        ;;
    all)
        run_frontend_tests
        echo ""
        run_backend_tests
        echo ""
        run_gateway_tests
        echo ""
        echo "=== All Tests Passed ==="
        ;;
    *)
        echo "Usage: $0 [frontend|backend|gateway|all]"
        exit 1
        ;;
esac
