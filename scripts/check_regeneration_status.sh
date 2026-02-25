#!/bin/bash
# Quick script to check regeneration progress

echo "🔄 Fingerprint Regeneration Status"
echo "=================================="
echo ""

# Check if process is running
if ps aux | grep -E "regenerate_youtube" | grep -v grep > /dev/null; then
    echo "✅ Process: RUNNING"
    ps aux | grep -E "regenerate_youtube" | grep -v grep | awk '{print "   PID:", $2, "| CPU:", $3"%", "| Memory:", $4"%"}'
else
    echo "❌ Process: NOT RUNNING"
fi

echo ""

# Check database
cd "$(dirname "$0")/.."
if [ -f "backend/data/models/fingerprint_index.faiss" ]; then
    python -c "
from backend.app.fingerprint_service import FingerprintService
fs = FingerprintService()
stats = fs.get_stats()
print(f'📊 Database:')
print(f'   Total fingerprints: {stats[\"total_fingerprints\"]}')
print(f'   Unique artists: {stats[\"artists\"]}')
if stats['artist_list']:
    print(f'   Recent: {stats[\"artist_list\"][-5:]}')
" 2>/dev/null || echo "   ⏳ Loading..."
else
    echo "📊 Database: Index file not created yet (still processing)"
fi

echo ""
echo "📝 Latest log entries:"
tail -5 /tmp/regenerate_full.log 2>/dev/null | grep -E "Processing|Added|Saved|✅" || echo "   (No recent activity)"
