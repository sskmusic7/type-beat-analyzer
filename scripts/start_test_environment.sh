#!/bin/bash
# Start backend and frontend for local testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=============================================="
echo "🧪 Starting Test Environment"
echo "=============================================="

# Activate conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate typebeat 2>/dev/null || {
    echo "⚠️  Conda environment 'typebeat' not found, using system Python"
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Cleanup complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo ""
echo "🚀 Starting Backend (FastAPI) on http://localhost:8000"
cd "$PROJECT_ROOT/backend"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/backend_test.log" 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Logs: backend_test.log"

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend failed to start"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Start Frontend
echo ""
echo "💻 Starting Frontend (Next.js) on http://localhost:3000"
cd "$PROJECT_ROOT/frontend"
npm run dev > "$PROJECT_ROOT/frontend_test.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
echo "   Logs: frontend_test.log"

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Frontend may still be starting..."
    fi
    sleep 1
done

echo ""
echo "=============================================="
echo "✅ Test Environment Ready!"
echo "=============================================="
echo ""
echo "📊 Backend:  http://localhost:8000"
echo "💻 Frontend: http://localhost:3000"
echo "📝 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait
