#!/usr/bin/env bash
# =============================================================================
# DB Backup Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

source "$PROJECT_DIR/.env" 2>/dev/null || true

mkdir -p "$BACKUP_DIR"

echo "=== Database Backup ==="
echo "Timestamp: $TIMESTAMP"

# Full backup
BACKUP_FILE="$BACKUP_DIR/robot_ai_db_${TIMESTAMP}.sql.gz"
docker compose exec -T postgres pg_dump \
    -U "${POSTGRES_USER:-robot_app}" \
    -d "${POSTGRES_DB:-robot_ai_db}" \
    --format=plain \
    --no-owner \
    --no-privileges | gzip > "$BACKUP_FILE"

echo "✓ Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "robot_ai_db_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
echo "✓ Cleanup complete"

# List current backups
echo ""
echo "Current backups:"
ls -lh "$BACKUP_DIR"/robot_ai_db_*.sql.gz 2>/dev/null || echo "  (none)"
