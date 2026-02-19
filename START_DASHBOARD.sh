#!/bin/bash
# Quick script to start the training dashboard

cd ml
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate typebeat

echo "🚀 Starting Training Dashboard..."
echo "📊 Open: http://localhost:8501"
echo ""
streamlit run training_dashboard.py
