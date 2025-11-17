#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "Virtual environment not found. Create one before running dev.sh" >&2
  exit 1
fi

source "$ROOT_DIR/.venv/bin/activate"

export PYTHONPATH="$ROOT_DIR/backend"
uvicorn app.main:app --app-dir "$ROOT_DIR/backend" --reload
