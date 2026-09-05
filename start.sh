#!/usr/bin/env bash
# ==============================================================================
# WeatherGPT — Unified Startup Runner (Smart India Hackathon)
# Starts FastAPI Backend (Port 8000) & React Vite Frontend (Port 5174) concurrently
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🌦️  Starting WeatherGPT Intelligence Platform..."
echo "=================================================="

# Function to cleanly stop both processes on Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Shutting down WeatherGPT services..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "👋 WeatherGPT stopped cleanly."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 1. Check & activate Python virtual environment
if [ -d "$BACKEND_DIR/venv" ]; then
    PYTHON_EXEC="$BACKEND_DIR/venv/bin/python"
elif [ -d "$BACKEND_DIR/.venv" ]; then
    PYTHON_EXEC="$BACKEND_DIR/.venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

echo "🐍 Starting FastAPI Backend on http://0.0.0.0:8000..."
cd "$BACKEND_DIR"
PYTHONPATH="$BACKEND_DIR" PORT=8000 "$PYTHON_EXEC" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 1.5

# 2. Start Vite Frontend
echo "⚡ Starting Vite Frontend on http://localhost:5174..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=================================================="
echo "✅ WeatherGPT is live and running!"
echo "   🌐 Frontend: http://localhost:5174"
echo "   📡 Backend:  http://localhost:8000/api/health"
echo "   📚 Docs:     http://localhost:8000/docs"
echo "=================================================="
echo "Press Ctrl+C to terminate both servers."

wait
