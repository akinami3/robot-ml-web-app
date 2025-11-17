#!/bin/bash

# Database setup script

set -e

echo "🗄️  Setting up PostgreSQL database..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
POSTGRES_USER=${POSTGRES_USER:-robot_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-robot_password}
POSTGRES_DB=${POSTGRES_DB:-robot_ml_db}

# Start PostgreSQL if not running
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "Starting PostgreSQL container..."
    docker-compose up -d postgres
    
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Run migrations
echo "Running Alembic migrations..."
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt
alembic upgrade head

echo "✅ Database setup complete!"
