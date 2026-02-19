#!/bin/bash
# Full system test - upload a beat and see the flow

echo "🧪 Type Beat Analyzer - Full System Test"
echo "=========================================="
echo ""

# Check if backend is running
echo "1️⃣  Checking Backend..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "   ✅ Backend is running on http://localhost:8000"
else
    echo "   ❌ Backend is NOT running"
    echo "   Start it with:"
    echo "   cd backend && /opt/miniconda3/envs/typebeat/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000"
    echo ""
    exit 1
fi

# Check if frontend is running
echo ""
echo "2️⃣  Checking Frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend is running on http://localhost:3000"
else
    echo "   ❌ Frontend is NOT running"
    echo "   Start it with:"
    echo "   cd frontend && npm run dev"
    echo ""
    exit 1
fi

# Test backend health
echo ""
echo "3️⃣  Testing Backend Health..."
HEALTH=$(curl -s http://localhost:8000/ | jq -r '.status' 2>/dev/null || echo "error")
if [ "$HEALTH" = "ok" ]; then
    echo "   ✅ Backend health check passed"
else
    echo "   ⚠️  Backend responded but status unclear"
fi

# Test trending endpoint
echo ""
echo "4️⃣  Testing Trending Endpoint..."
TRENDING=$(curl -s http://localhost:8000/api/trending | jq -r '.artists | length' 2>/dev/null || echo "0")
if [ "$TRENDING" -gt "0" ]; then
    echo "   ✅ Trending endpoint working ($TRENDING artists)"
else
    echo "   ⚠️  No trending data (might be normal if cache is empty)"
fi

# Check API credentials
echo ""
echo "5️⃣  Checking API Credentials..."
cd "$(dirname "$0")/.."

if grep -q "ACOUSTID_API_KEY=" backend/.env && ! grep -q "ACOUSTID_API_KEY=$" backend/.env; then
    echo "   ✅ AcoustID API key configured"
else
    echo "   ❌ AcoustID API key missing"
fi

if grep -q "ACRCLOUD_ACCESS_KEY=" backend/.env && ! grep -q "ACRCLOUD_ACCESS_KEY=$" backend/.env; then
    echo "   ✅ ACRCloud credentials configured"
else
    echo "   ❌ ACRCloud credentials missing"
fi

if grep -q "AUDDIO_API_TOKEN=" backend/.env && ! grep -q "AUDDIO_API_TOKEN=$" backend/.env; then
    echo "   ✅ AudD.io API token configured"
else
    echo "   ❌ AudD.io API token missing"
fi

echo ""
echo "=========================================="
echo "✅ System is ready for testing!"
echo ""
echo "📱 Open your browser:"
echo "   http://localhost:3000"
echo ""
echo "🎵 To test:"
echo "   1. Drag & drop an audio file (MP3, WAV, etc.)"
echo "   2. Watch the processing stages"
echo "   3. See results with artist matches"
echo ""
echo "🔍 Monitor backend logs to see:"
echo "   - File upload"
echo "   - Database queries (AcoustID, ACRCloud, AudD)"
echo "   - Local fingerprint search"
echo "   - Trending data fetch"
echo ""
