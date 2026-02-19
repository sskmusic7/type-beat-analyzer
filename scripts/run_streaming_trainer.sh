#!/bin/bash
# Automated streaming trainer runner
# Streams from Spotify, generates fingerprints, trains model

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Automated Streaming Trainer${NC}"

# Check if we're in the right directory
if [ ! -f "ml/streaming_trainer.py" ]; then
    echo -e "${RED}Error: Must run from project root${NC}"
    exit 1
fi

# Check for Spotify credentials
if [ -z "$SPOTIFY_CLIENT_ID" ] || [ -z "$SPOTIFY_CLIENT_SECRET" ]; then
    echo -e "${YELLOW}⚠️  Spotify credentials not found in environment${NC}"
    echo -e "${YELLOW}   Checking backend/.env...${NC}"
    
    if [ -f "backend/.env" ]; then
        source backend/.env
        export SPOTIFY_CLIENT_ID
        export SPOTIFY_CLIENT_SECRET
    fi
    
    if [ -z "$SPOTIFY_CLIENT_ID" ] || [ -z "$SPOTIFY_CLIENT_SECRET" ]; then
        echo -e "${RED}❌ Spotify credentials required!${NC}"
        echo -e "${YELLOW}   Get them from: https://developer.spotify.com/dashboard${NC}"
        echo -e "${YELLOW}   Add to backend/.env:${NC}"
        echo -e "   SPOTIFY_CLIENT_ID=your_client_id"
        echo -e "   SPOTIFY_CLIENT_SECRET=your_client_secret"
        exit 1
    fi
fi

# Default artists if not provided
ARTISTS="${@:-Drake Travis\ Scott Metro\ Boomin Playboi\ Carti}"

echo -e "${GREEN}📝 Training on artists: ${ARTISTS}${NC}"
echo -e "${GREEN}📊 Max tracks per artist: 50${NC}"
echo ""

# Activate conda environment if available
if command -v conda &> /dev/null; then
    echo -e "${YELLOW}🐍 Activating conda environment...${NC}"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate typebeat 2>/dev/null || echo -e "${YELLOW}   (No conda env found, using system Python)${NC}"
fi

# Install dependencies if needed
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
cd ml
python -c "import spotipy, requests" 2>/dev/null || {
    echo -e "${YELLOW}   Installing missing dependencies...${NC}"
    pip install spotipy requests python-dotenv faiss-cpu -q
}

# Run trainer
echo -e "${GREEN}🎵 Starting training...${NC}"
echo ""

python streaming_trainer.py \
    --artists $ARTISTS \
    --tracks-per-artist 50

echo ""
echo -e "${GREEN}✅ Training complete!${NC}"
echo -e "${GREEN}📁 Fingerprints saved to: data/training_fingerprints/${NC}"
