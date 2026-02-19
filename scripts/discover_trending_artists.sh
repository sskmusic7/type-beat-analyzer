#!/bin/bash
# Quick script to discover trending type beat artists

cd "$(dirname "$0")/.."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate typebeat

echo "🔍 Discovering trending type beat artists..."
echo ""

python ml/discover_trending_artists.py --max-artists 100 --top-n 50 --save

echo ""
echo "✅ Done! Check data/trending_artists.json for results"
