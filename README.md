# Type Beat Analyzer 🎵

**A Shazam for type beats** that tells producers "Your beat sounds like a [Artist] type beat" + shows you who's trending so you can optimize for the market.

## The Vision

This solves TWO critical problems for producers:

1. **Creative validation** - "Does my beat actually sound like what I'm going for?"
2. **Market intelligence** - "Who should I be making beats for RIGHT NOW?"

## Technical Stack

### Backend
- **FastAPI** - Python API for ML inference
- **PyTorch** - Model training and inference
- **librosa** - Audio feature extraction
- **FAISS** - Fast similarity search (from Neural Audio FP)
- **PostgreSQL** - Database for fingerprints + metadata
- **Redis** - Cache for trending data

### Frontend
- **Next.js** + **TypeScript** - Modern web app
- **TailwindCSS** - Styling
- **Web Audio API** - Browser audio processing

### ML Pipeline
- **Neural Audio Fingerprint** - Base model (ICASSP 2021)
- **Custom CNN** - Type beat classification layer
- **YouTube Data API v3** - Trending intelligence

### Services
- **AWS S3** - Audio file storage
- **YouTube Data API** - Trending metrics
- **Railway/Vercel** - Hosting (MVP)

## Project Structure

```
.
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── ml/              # Model training pipeline
├── data/            # Datasets and models
│   ├── raw/         # Raw audio files
│   ├── processed/   # Processed features
│   └── models/      # Trained models
├── scripts/         # Utility scripts
├── neural-audio-fp/ # Neural Audio FP reference
└── dejavu-reference/ # Dejavu reference
```

## MVP Timeline

- **Week 1-2**: Audio feature extraction + YouTube API integration
- **Week 3-4**: Train initial model on top 15 artists
- **Week 5-6**: Build web app + mobile upload flow
- **Week 7-8**: Beta with 50 producers, refine model

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### ML Training

```bash
cd ml
python train_model.py --artists drake travis metro-boomin
```

## Research Foundation

This project builds on:

- **Neural Audio Fingerprint** (ICASSP 2021) - Contrastive learning for robust audio fingerprints
- **Music Genre Classification CNNs** - Proven 75-80% accuracy on GTZAN dataset
- **Artist Similarity Research** - Quantifying style and mood similarities

## Business Model

- **Freemium**: 3 scans/month free, unlimited for £9.99/mo
- **Pro Tier** (£29.99/mo): Trend alerts, batch analysis, export reports
- **B2B**: License to beat platforms (BeatStars, Airbit)

## License

MIT
