#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source "$ROOT_DIR/.venv/bin/activate"
ruff check "$ROOT_DIR/backend"
cd "$ROOT_DIR/frontend" && npm run lint
