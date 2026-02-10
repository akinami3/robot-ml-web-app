#!/bin/bash
# ===========================================
# Proto Sync Script
# ===========================================
# Copies the canonical proto/fleet.proto to service-specific directories
# used by Docker builds. Run this after editing proto/fleet.proto.
#
# Usage: ./scripts/sync-proto.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE="${PROJECT_ROOT}/proto/fleet.proto"

if [[ ! -f "$SOURCE" ]]; then
    echo "ERROR: Source proto not found at ${SOURCE}" >&2
    exit 1
fi

TARGETS=(
    "${PROJECT_ROOT}/gateway/proto/fleet.proto"
    "${PROJECT_ROOT}/backend/proto/fleet.proto"
)

for target in "${TARGETS[@]}"; do
    cp "$SOURCE" "$target"
    echo "Synced: $target"
done

echo "Proto sync complete."
