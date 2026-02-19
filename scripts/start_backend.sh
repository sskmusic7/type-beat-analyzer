#!/bin/bash

# Start backend with conda Python (librosa support)

cd "$(dirname "$0")/../backend"

# Use conda Python directly
CONDA_PYTHON="/opt/miniconda3/envs/typebeat/bin/python"

if [ ! -f "$CONDA_PYTHON" ]; then
    echo "❌ Conda Python not found at $CONDA_PYTHON"
    echo "   Make sure conda environment 'typebeat' exists"
    exit 1
fi

# Check if librosa is available
if ! $CONDA_PYTHON -c "import librosa" 2>/dev/null; then
    echo "⚠️  librosa not found. Installing..."
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate typebeat
    conda install -c conda-forge librosa -y
    pip install soundfile
fi

echo "🚀 Starting backend with librosa support..."
echo "   Using: $CONDA_PYTHON"
echo "   URL: http://localhost:8000"
echo ""

$CONDA_PYTHON -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
