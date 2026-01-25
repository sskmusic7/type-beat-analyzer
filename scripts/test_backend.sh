#!/bin/bash

# Backend Testing Script
# Tests all backend endpoints via CLI

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
ERRORS=0

echo "🧪 Testing Backend API: $BACKEND_URL"
echo "======================================"

# Test 1: Health Check
echo ""
echo "[1] Health Check..."
HEALTH=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/" 2>&1)
HTTP_CODE=$(echo "$HEALTH" | tail -n1)
BODY=$(echo "$HEALTH" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check passed (HTTP $HTTP_CODE)"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    ERRORS=$((ERRORS + 1))
fi

# Test 2: Trending Endpoint
echo ""
echo "[2] Trending Artists Endpoint..."
TRENDING=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/trending?limit=5" 2>&1)
HTTP_CODE=$(echo "$TRENDING" | tail -n1)
BODY=$(echo "$TRENDING" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Trending endpoint passed (HTTP $HTTP_CODE)"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    
    # Validate response structure
    if echo "$BODY" | jq -e '. | type == "array"' >/dev/null 2>&1; then
        echo "✅ Response is valid JSON array"
    else
        echo "⚠️  Response structure may be unexpected"
    fi
else
    echo "❌ Trending endpoint failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    ERRORS=$((ERRORS + 1))
fi

# Test 3: Specific Artist Trending
echo ""
echo "[3] Artist Trending Endpoint..."
ARTIST_TRENDING=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/artists/Drake/trending" 2>&1)
HTTP_CODE=$(echo "$ARTIST_TRENDING" | tail -n1)
BODY=$(echo "$ARTIST_TRENDING" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Artist trending endpoint passed (HTTP $HTTP_CODE)"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
else
    echo "❌ Artist trending endpoint failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    ERRORS=$((ERRORS + 1))
fi

# Test 4: Analyze Endpoint (with test file if available)
echo ""
echo "[4] Analyze Endpoint..."
if [ -f "test_audio.wav" ] || [ -f "../test_audio.wav" ]; then
    TEST_FILE=$(find . -name "test_audio.wav" -o -name "../test_audio.wav" | head -1)
    echo "Testing with file: $TEST_FILE"
    ANALYZE=$(curl -s -w "\n%{http_code}" -X POST \
        -F "file=@$TEST_FILE" \
        "$BACKEND_URL/api/analyze" 2>&1)
    HTTP_CODE=$(echo "$ANALYZE" | tail -n1)
    BODY=$(echo "$ANALYZE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Analyze endpoint passed (HTTP $HTTP_CODE)"
        echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    else
        echo "❌ Analyze endpoint failed (HTTP $HTTP_CODE)"
        echo "$BODY"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "⚠️  No test audio file found, skipping analyze test"
    echo "   (Create test_audio.wav to test audio upload)"
fi

# Summary
echo ""
echo "======================================"
echo "📊 Backend Test Summary"
echo "======================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ $ERRORS test(s) failed"
    exit 1
fi
