#!/bin/bash
# Check training progress

cd "$(dirname "$0")/.."

echo "📊 Training Progress Check"
echo "=========================="
echo ""

# Check if training is running
if pgrep -f "clean_and_train.py" > /dev/null; then
    echo "✅ Training is RUNNING"
    echo ""
    echo "📝 Latest log entries:"
    tail -20 ml/training_log.txt 2>/dev/null || echo "   Log file not found yet"
else
    echo "⏸️  Training is NOT running"
    echo ""
    echo "📝 Last log entries:"
    tail -20 ml/training_log.txt 2>/dev/null || echo "   No log file found"
fi

echo ""
echo "📁 Check results:"
if [ -f "ml/data/training_fingerprints/final_training_data_1000.json" ]; then
    count=$(python -c "import json; data=json.load(open('ml/data/training_fingerprints/final_training_data_1000.json')); print(len(data))" 2>/dev/null || echo "0")
    echo "   ✅ Final file exists: $count fingerprints"
else
    echo "   ⏳ Final file not created yet"
fi

# Check batch files
batch_count=$(ls ml/data/training_fingerprints/training_batch_*.json 2>/dev/null | wc -l | tr -d ' ')
if [ "$batch_count" -gt 0 ]; then
    echo "   📦 Batch files: $batch_count checkpoints found"
    latest_batch=$(ls -t ml/data/training_fingerprints/training_batch_*.json 2>/dev/null | head -1)
    if [ -n "$latest_batch" ]; then
        latest_count=$(python -c "import json; data=json.load(open('$latest_batch')); print(len(data))" 2>/dev/null || echo "0")
        echo "   📊 Latest batch: $latest_count fingerprints"
    fi
fi

echo ""
echo "🎯 Target: 1,080 fingerprints (108 artists × 10 each)"
