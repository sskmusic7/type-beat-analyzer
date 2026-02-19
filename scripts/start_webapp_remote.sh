#!/bin/bash
# Start Full Web App (Backend + Frontend) - REMOTE ACCESS
# Binds to 0.0.0.0 so you can access from other devices on your network

set -e
cd "$(dirname "$0")/.."

# Get local IP for display
LOCAL_IP="localhost"
if command -v hostname &> /dev/null; then
  LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi
if [ -z "$LOCAL_IP" ] && command -v ipconfig &> /dev/null; then
  LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null)
fi
[ -z "$LOCAL_IP" ] && LOCAL_IP="localhost"

# Activate conda for backend
activate_conda() {
  if command -v conda &> /dev/null; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate typebeat 2>/dev/null || true
  fi
}

# Cleanup on exit
cleanup() {
  echo ""
  echo "🛑 Shutting down..."
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "=============================================="
echo "🎵 Type Beat Web App - REMOTE MODE"
echo "=============================================="
echo ""

# Start Backend
echo "🚀 Starting Backend (port 8000)..."
activate_conda
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
sleep 3

# Start Frontend
echo "🚀 Starting Frontend (port 3000)..."
cd frontend
npm run dev:remote &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready
sleep 5

echo ""
echo "=============================================="
echo "✅ Both services running!"
echo "=============================================="
echo ""
echo "📊 Web App (upload beats):"
echo "   This machine:  http://localhost:3000"
echo "   Other devices: http://${LOCAL_IP}:3000"
echo ""
echo "🔧 Backend API:"
echo "   This machine:  http://localhost:8000"
echo "   Other devices: http://${LOCAL_IP}:8000"
echo ""
echo "Press Ctrl+C to stop both services"
echo "=============================================="
echo ""

# Wait for either process to exit
wait
