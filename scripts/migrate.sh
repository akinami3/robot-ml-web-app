#!/usr/bin/env bash
# =============================================================================
# DB Migration Script
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ACTION="${1:-upgrade}"
ARGS="${2:-head}"

cd "$PROJECT_DIR"

case "$ACTION" in
    upgrade)
        echo "Running migrations (upgrade to $ARGS)..."
        docker compose exec backend alembic upgrade "$ARGS"
        ;;
    downgrade)
        echo "Rolling back migrations (downgrade to $ARGS)..."
        docker compose exec backend alembic downgrade "$ARGS"
        ;;
    create)
        if [ -z "$ARGS" ] || [ "$ARGS" = "head" ]; then
            echo "Usage: $0 create \"migration description\""
            exit 1
        fi
        echo "Creating migration: $ARGS"
        docker compose exec backend alembic revision --autogenerate -m "$ARGS"
        ;;
    current)
        docker compose exec backend alembic current
        ;;
    history)
        docker compose exec backend alembic history --verbose
        ;;
    *)
        echo "Usage: $0 [upgrade|downgrade|create|current|history] [args]"
        echo ""
        echo "Examples:"
        echo "  $0 upgrade head           # Apply all migrations"
        echo "  $0 downgrade -1           # Rollback last migration"
        echo "  $0 create \"add users\"     # Create new migration"
        echo "  $0 current                # Show current revision"
        echo "  $0 history                # Show migration history"
        exit 1
        ;;
esac
