#!/usr/bin/env bash
# =============================================================================
# Proto Generation Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROTO_DIR="$PROJECT_DIR/proto"

echo "=== Generating Protocol Buffer code ==="

# Python (Backend)
PYTHON_OUT="$PROJECT_DIR/backend/app/infrastructure/grpc/proto"
mkdir -p "$PYTHON_OUT"
touch "$PYTHON_OUT/__init__.py"

echo "Generating Python code..."
python -m grpc_tools.protoc \
    -I "$PROTO_DIR" \
    --python_out="$PYTHON_OUT" \
    --grpc_python_out="$PYTHON_OUT" \
    --pyi_out="$PYTHON_OUT" \
    "$PROTO_DIR"/*.proto

echo "✓ Python proto files generated in $PYTHON_OUT"

# Go (Gateway)
GO_OUT="$PROJECT_DIR/gateway/internal/bridge/proto"
mkdir -p "$GO_OUT"

echo "Generating Go code..."
protoc \
    -I "$PROTO_DIR" \
    --go_out="$GO_OUT" --go_opt=paths=source_relative \
    --go-grpc_out="$GO_OUT" --go-grpc_opt=paths=source_relative \
    "$PROTO_DIR"/*.proto

echo "✓ Go proto files generated in $GO_OUT"
echo ""
echo "=== Proto generation complete ==="
