#!/bin/bash

# Debug Loop Script - Runs 5 iterations of testing and fixing
# Tests backend via CLI and frontend via Playwright audit agents

set -e

MAX_ITERATIONS=5
ITERATION=1
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
AUDIT_DIR="../audit-agents/frontend-audit"
LOG_DIR="debug_logs"
mkdir -p "$LOG_DIR"

echo "🔍 Starting Debug Loop - 5 Iterations"
echo "======================================"

while [ $ITERATION -le $MAX_ITERATIONS ]; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 ITERATION $ITERATION of $MAX_ITERATIONS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    LOG_FILE="$LOG_DIR/iteration_${ITERATION}.log"
    ERROR_FILE="$LOG_DIR/iteration_${ITERATION}_errors.log"
    
    # Test 1: Backend Health Check
    echo "[$ITERATION.1] Testing Backend Health..."
    if curl -s -f "$BACKEND_URL/" > /dev/null 2>&1; then
        echo "✅ Backend is running"
        curl -s "$BACKEND_URL/" | jq '.' > "$LOG_FILE" 2>&1 || echo "Backend response received"
    else
        echo "❌ Backend is NOT running - starting it..."
        cd backend
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install -q -r requirements.txt
        uvicorn main:app --reload --host 0.0.0.0 --port 8000 > "../$LOG_DIR/backend_${ITERATION}.log" 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > "../$LOG_DIR/backend_${ITERATION}.pid"
        sleep 5
        cd ..
    fi
    
    # Test 2: Backend API Endpoints
    echo "[$ITERATION.2] Testing Backend API Endpoints..."
    
    # Test /api/trending
    echo "  → Testing /api/trending..."
    TRENDING_RESPONSE=$(curl -s "$BACKEND_URL/api/trending?limit=5" 2>&1)
    if echo "$TRENDING_RESPONSE" | grep -q "error\|Error\|ERROR" 2>/dev/null; then
        echo "  ❌ Trending endpoint error: $TRENDING_RESPONSE" | tee -a "$ERROR_FILE"
    else
        echo "  ✅ Trending endpoint working"
        echo "$TRENDING_RESPONSE" | jq '.' > "$LOG_DIR/trending_${ITERATION}.json" 2>&1 || echo "$TRENDING_RESPONSE" > "$LOG_DIR/trending_${ITERATION}.txt"
    fi
    
    # Test 3: Frontend (if running)
    echo "[$ITERATION.3] Testing Frontend..."
    if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
        echo "  ✅ Frontend is running"
        
        # Run Playwright audit
        if [ -d "$AUDIT_DIR" ]; then
            echo "  → Running Playwright audit..."
            cd "$AUDIT_DIR"
            if [ ! -d "node_modules" ]; then
                npm install --silent
                npx playwright install chromium --with-deps 2>/dev/null || true
            fi
            BASE_URL="$FRONTEND_URL" HEADLESS=true node audit.js > "../../$LOG_DIR/frontend_audit_${ITERATION}.log" 2>&1
            AUDIT_EXIT=$?
            if [ $AUDIT_EXIT -eq 0 ]; then
                echo "  ✅ Frontend audit passed"
            else
                echo "  ❌ Frontend audit found issues - check $LOG_DIR/frontend_audit_${ITERATION}.log" | tee -a "../../$ERROR_FILE"
            fi
            cd ../..
        else
            echo "  ⚠️  Audit agents not found at $AUDIT_DIR"
        fi
    else
        echo "  ⚠️  Frontend is NOT running (start with: cd frontend && npm run dev)"
    fi
    
    # Test 4: Backend Code Quality
    echo "[$ITERATION.4] Checking Backend Code Quality..."
    cd backend
    source venv/bin/activate 2>/dev/null || true
    
    # Check for Python syntax errors
    echo "  → Checking Python syntax..."
    python3 -m py_compile app/*.py main.py 2>&1 | tee -a "../$ERROR_FILE" || echo "  ✅ No syntax errors"
    
    # Check imports
    echo "  → Checking imports..."
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.audio_processor import AudioProcessor
    from app.model_inference import ModelInference
    from app.trending_service import TrendingService
    print('  ✅ All imports working')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    sys.exit(1)
" 2>&1 | tee -a "../$ERROR_FILE"
    
    cd ..
    
    # Test 5: Frontend Code Quality
    echo "[$ITERATION.5] Checking Frontend Code Quality..."
    if [ -d "frontend" ]; then
        cd frontend
        if [ -d "node_modules" ]; then
            echo "  → Checking TypeScript compilation..."
            npx tsc --noEmit 2>&1 | tee -a "../$LOG_DIR/tsc_${ITERATION}.log" || echo "  ✅ TypeScript check complete"
        fi
        cd ..
    fi
    
    # Summary
    echo ""
    echo "📊 Iteration $ITERATION Summary:"
    if [ -f "$ERROR_FILE" ] && [ -s "$ERROR_FILE" ]; then
        echo "  ❌ Issues found - see $ERROR_FILE"
        ERROR_COUNT=$(wc -l < "$ERROR_FILE" 2>/dev/null || echo "0")
        echo "  📝 Error count: $ERROR_COUNT"
    else
        echo "  ✅ No critical errors detected"
    fi
    
    # If errors found, attempt fixes (this would be expanded with actual fix logic)
    if [ -f "$ERROR_FILE" ] && [ -s "$ERROR_FILE" ]; then
        echo "  🔧 Analyzing errors for fixes..."
        # Error analysis and auto-fix logic would go here
    fi
    
    ITERATION=$((ITERATION + 1))
    
    if [ $ITERATION -le $MAX_ITERATIONS ]; then
        echo "  ⏳ Waiting 3 seconds before next iteration..."
        sleep 3
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Debug Loop Complete - 5 Iterations Finished"
echo "📁 Logs saved in: $LOG_DIR/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
