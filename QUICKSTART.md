# Quick Start Guide 🚀

Get the Type Beat Analyzer up and running in minutes!

## Prerequisites

- Python 3.8+ 
- Node.js 18+
- PostgreSQL (optional for MVP - can use SQLite)
- Redis (optional for MVP - trending data will use mock)

## Setup

### Option 1: Automated Setup (Recommended)

```bash
./scripts/setup.sh
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend

```bash
cd frontend
npm install
```

#### ML Training (Optional)

```bash
cd ml
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

1. Copy environment template:
```bash
cp backend/.env.example backend/.env
```

2. Edit `backend/.env` and add:
   - `YOUTUBE_API_KEY` - Get from [Google Cloud Console](https://console.cloud.google.com/)
   - `DATABASE_URL` - PostgreSQL connection string (or leave default for SQLite)
   - `REDIS_HOST` - Redis host (default: localhost)

## Running the Application

### Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will run on `http://localhost:3000`

## Training Your First Model

### Step 1: Collect Training Data

Download type beats from YouTube:

```bash
cd scripts
python download_type_beats.py --artists Drake "Travis Scott" "Metro Boomin" --max_per_artist 50
```

This will download beats to `data/raw/` organized by artist.

### Step 2: Train the Model

```bash
cd ml
source venv/bin/activate
python train_model.py \
  --artists Drake "Travis Scott" "Metro Boomin" \
  --epochs 50 \
  --batch_size 32 \
  --data_dir ../data/raw
```

The trained model will be saved to `data/models/type_beat_classifier.pt`

### Step 3: Update Backend

Copy the model to the backend's expected location:

```bash
cp data/models/type_beat_classifier.pt backend/data/models/
```

Or update `MODEL_PATH` in `backend/.env`

## Testing

### Test Backend API

```bash
curl http://localhost:8000/
```

### Test Audio Upload

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@/path/to/your/beat.mp3"
```

## Project Structure

```
.
├── backend/          # FastAPI backend
│   ├── app/         # Application modules
│   │   ├── audio_processor.py    # Feature extraction
│   │   ├── model_inference.py    # ML inference
│   │   ├── trending_service.py   # YouTube API integration
│   │   └── schemas.py            # API schemas
│   └── main.py      # FastAPI app
├── frontend/         # Next.js frontend
│   ├── app/         # Next.js app directory
│   ├── components/  # React components
│   └── types/       # TypeScript types
├── ml/              # Model training
│   └── train_model.py
├── scripts/         # Utility scripts
│   └── download_type_beats.py
└── data/           # Data storage
    ├── raw/        # Raw audio files
    ├── processed/  # Processed features
    └── models/     # Trained models
```

## Next Steps

1. **Collect more training data** - More artists = better model
2. **Fine-tune hyperparameters** - Adjust batch size, learning rate, etc.
3. **Add more artists** - Expand beyond initial 15-20
4. **Deploy** - Use Railway, Vercel, or AWS

## Troubleshooting

### Backend won't start
- Check Python version: `python3 --version` (need 3.8+)
- Ensure all dependencies installed: `pip install -r requirements.txt`

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Clear cache: `rm -rf node_modules .next && npm install`

### Model training fails
- Ensure you have GPU with CUDA (or use CPU - slower)
- Check data directory has audio files organized by artist
- Reduce batch size if out of memory

### YouTube API errors
- Verify API key is correct
- Check API quota limits
- Trending features will use mock data if API unavailable

## Resources

- [Neural Audio Fingerprint Paper](https://arxiv.org/abs/2010.11910)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [YouTube Data API](https://developers.google.com/youtube/v3)
