#!/bin/bash
# Setup script for streaming trainer
# Installs dependencies and verifies setup

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 Setting up Streaming Trainer${NC}"

# Check Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi

# Activate conda if available
if command -v conda &> /dev/null; then
    echo -e "${YELLOW}🐍 Activating conda environment...${NC}"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate typebeat 2>/dev/null || echo -e "${YELLOW}   (No conda env found, using system Python)${NC}"
fi

# Install dependencies
echo -e "${GREEN}📦 Installing dependencies...${NC}"
cd ml
pip install spotipy requests python-dotenv faiss-cpu -q

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check Spotify credentials
echo -e "${YELLOW}🔑 Checking Spotify credentials...${NC}"
if [ -f "../backend/.env" ]; then
    source ../backend/.env
    if [ -n "$SPOTIFY_CLIENT_ID" ] && [ -n "$SPOTIFY_CLIENT_SECRET" ]; then
        echo -e "${GREEN}✅ Spotify credentials found${NC}"
    else
        echo -e "${YELLOW}⚠️  Spotify credentials not set in backend/.env${NC}"
        echo -e "${YELLOW}   Get them from: https://developer.spotify.com/dashboard${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  backend/.env not found${NC}"
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${GREEN}   Run: ./scripts/run_streaming_trainer.sh${NC}"
