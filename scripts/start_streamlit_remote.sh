#!/bin/bash
# Start Streamlit Training Dashboard - REMOTE ACCESS
# Binds to 0.0.0.0 so you can access from other devices on your network

cd "$(dirname "$0")/.."
cd ml

# Activate conda if available
if command -v conda &> /dev/null; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate typebeat 2>/dev/null || true
fi

# Get local IP for display (Mac/Linux)
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}' || echo "YOUR_IP")

echo "=============================================="
echo "🎵 Type Beat Training Dashboard - REMOTE MODE"
echo "=============================================="
echo ""
echo "📊 Access from this machine:  http://localhost:8501"
echo "📱 Access from other devices:  http://${LOCAL_IP}:8501"
echo ""
echo "Press Ctrl+C to stop"
echo "=============================================="
echo ""

streamlit run training_dashboard.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
