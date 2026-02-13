#!/usr/bin/env bash
# =============================================================================
# Setup Script - Initial environment setup
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Robot AI Web Application - Setup ==="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker >= 24.0"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "ERROR: Docker Compose is not available. Please install Docker Compose >= 2.20"
    exit 1
fi

echo "✓ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')"
echo "✓ Docker Compose $(docker compose version --short)"

# Create .env if not exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "Creating .env from .env.example..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "✓ .env created. Please review and update passwords."
else
    echo "✓ .env already exists"
fi

# Generate JWT RSA keys if not exists
if [ ! -d "$PROJECT_DIR/keys" ]; then
    echo ""
    echo "Generating JWT RSA keys..."
    mkdir -p "$PROJECT_DIR/keys"
    openssl genrsa -out "$PROJECT_DIR/keys/private.pem" 2048 2>/dev/null
    openssl rsa -in "$PROJECT_DIR/keys/private.pem" -pubout -out "$PROJECT_DIR/keys/public.pem" 2>/dev/null
    chmod 600 "$PROJECT_DIR/keys/private.pem"
    chmod 644 "$PROJECT_DIR/keys/public.pem"
    echo "✓ RSA keys generated in keys/"
else
    echo "✓ JWT RSA keys already exist"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p "$PROJECT_DIR/data/datasets"
mkdir -p "$PROJECT_DIR/data/models"
mkdir -p "$PROJECT_DIR/data/logs"
mkdir -p "$PROJECT_DIR/data/images"
mkdir -p "$PROJECT_DIR/uploads/ml"
mkdir -p "$PROJECT_DIR/backups"
echo "✓ Data directories created"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Review and update .env (especially passwords)"
echo "  2. Start services: ./scripts/dev.sh"
echo "  3. Pull LLM model: docker compose exec ollama ollama pull llama3"
echo ""
