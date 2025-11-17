#!/bin/bash

# Development startup script for Robot ML Web Application

set -e

echo "🚀 Starting Robot ML Web Application (Development Mode)"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration"
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/images/raw
mkdir -p data/images/processed
mkdir -p data/datasets
mkdir -p data/models/checkpoints
mkdir -p data/rag/embeddings
mkdir -p logs

# Start Docker Compose services
echo "🐳 Starting Docker Compose services..."
docker-compose up -d postgres mqtt-broker

# Wait for services to be ready
echo "⏳ Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U robot_user > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

echo "⏳ Waiting for MQTT Broker..."
sleep 3
echo "✅ MQTT Broker is ready"

# Run database migrations
echo "🗄️  Running database migrations..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -d "alembic/versions" ]; then
    echo "🔧 Initializing Alembic..."
    alembic init alembic
fi

alembic upgrade head
cd ..

# Start backend in development mode
echo "🔧 Starting Backend (FastAPI)..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend in development mode
echo "🎨 Starting Frontend (Vue.js)..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📊 Access URLs:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   PostgreSQL:   localhost:5432"
echo "   MQTT Broker:  localhost:1883"
echo ""
echo "Press Ctrl+C to stop all services"

# Handle Ctrl+C
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit 0" INT

# Keep script running
wait
