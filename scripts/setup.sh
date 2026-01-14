#!/bin/bash

# Setup script for Type Beat Analyzer
# Run this to set up the development environment

set -e

echo "🎵 Setting up Type Beat Analyzer..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/raw data/processed data/models
mkdir -p backend/logs
mkdir -p frontend/.next

# Backend setup
echo "🐍 Setting up Python backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Frontend setup
echo "⚛️  Setting up Next.js frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# ML setup
echo "🤖 Setting up ML environment..."
cd ml
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy backend/.env.example to backend/.env and add your API keys"
echo "2. Start the backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "3. Start the frontend: cd frontend && npm run dev"
echo "4. Visit http://localhost:3000"
echo ""
echo "To train a model:"
echo "  cd ml && source venv/bin/activate"
echo "  python train_model.py --artists Drake Travis\\ Scott Metro\\ Boomin"
