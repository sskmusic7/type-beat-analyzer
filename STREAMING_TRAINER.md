# Automated Streaming Trainer

## Overview

The streaming trainer automatically collects training data by:
1. **Streaming** 30-second previews from Spotify (legal)
2. **Generating fingerprints** from each preview
3. **Storing fingerprints only** (not audio files)
4. **Deleting audio immediately** after fingerprinting

This approach is **legal, ethical, and sustainable** because:
- ✅ Only uses Spotify's public 30-second previews
- ✅ Stores mathematical fingerprints (not copyrighted audio)
- ✅ Deletes audio files immediately
- ✅ No permanent storage of copyrighted material

## Setup

### ⚠️ Important: Spotify API Changes (February 2026)

**Development Mode Restrictions:**
- ✅ **Requires Spotify Premium account** (for Development Mode apps)
- ✅ Limited to **5 authorized users** per Client ID
- ✅ Limited to **smaller set of endpoints** (but `GET /search` is still available)
- ✅ All existing Development Mode apps affected starting **March 9, 2026**

**Good News:** Our streaming trainer uses `GET /search` which is **still available** ✅

See: [Spotify API Changes - February 2026](https://developer.spotify.com/documentation/web-api/references/changes/february-2026)

### 1. Get Spotify API Credentials

1. Go to: https://developer.spotify.com/dashboard
2. Click "Create an app"
3. Fill in:
   - **App name**: Type Beat Trainer
   - **App description**: Automated training data collection
   - **Redirect URI**: `http://localhost:3000/callback` (optional)
4. Click "Save"
5. Copy your **Client ID** and **Client Secret**

**Note:** You'll need a **Spotify Premium account** for Development Mode apps (new requirement as of February 2026)

### 2. Add to Environment

Add to `backend/.env`:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### 3. Install Dependencies

```bash
cd ml
pip install -r requirements.txt
```

Or install just the streaming dependencies:

```bash
pip install spotipy requests python-dotenv faiss-cpu
```

## Usage

### Option 1: Command Line Script

```bash
# Run from project root
./scripts/run_streaming_trainer.sh

# Or with custom artists
./scripts/run_streaming_trainer.sh "Drake" "Travis Scott" "Metro Boomin"
```

### Option 2: Direct Python

```bash
cd ml
python streaming_trainer.py \
    --artists "Drake" "Travis Scott" "Metro Boomin" "Playboi Carti" \
    --tracks-per-artist 50
```

### Option 3: Backend API Endpoint

```bash
curl -X POST "http://localhost:8000/api/train/streaming" \
  -F "artists=Drake" \
  -F "artists=Travis Scott" \
  -F "artists=Metro Boomin" \
  -F "max_tracks=50"
```

## What Gets Stored

**Stored (Legal):**
```json
{
  "fingerprint": [0.23, 0.45, 0.12, ..., 0.89],  // 128 numbers
  "artist": "Drake",
  "track_name": "God's Plan",
  "track_id": "spotify:track:...",
  "source": "spotify_streaming",
  "timestamp": 1704067200
}
```

**NOT Stored (Avoids Copyright):**
- ❌ Audio files (MP3, WAV, etc.)
- ❌ Full songs
- ❌ Any copyrighted audio content

## Output

Fingerprints are saved to:
```
data/training_fingerprints/training_fingerprints_<timestamp>.json
data/training_fingerprints/final_training_data.json
```

## Using Training Data

### For Model Training

```python
from ml.streaming_trainer import StreamingTrainer

trainer = StreamingTrainer()
trainer.load_training_data("final_training_data.json")
training_data = trainer.export_for_model_training()

# Use in PyTorch
fingerprints = training_data['fingerprints']  # numpy array
labels = training_data['labels']  # numpy array
artist_list = training_data['artist_list']  # list of artists
```

### For Fingerprint Database

The fingerprints can also be added directly to the FAISS index:

```python
from backend.app.fingerprint_service import FingerprintService

service = FingerprintService()
# Load training data and add each fingerprint
# (implementation depends on your needs)
```

## Automation

### Scheduled Training (Cron)

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/Type\ beat && ./scripts/run_streaming_trainer.sh
```

### Continuous Training

Run in background:

```bash
nohup ./scripts/run_streaming_trainer.sh > training.log 2>&1 &
```

## Rate Limiting

The trainer includes rate limiting:
- **0.5 seconds** between tracks
- **2 seconds** between artists

This ensures we don't hit API limits.

## Troubleshooting

### "Spotify credentials not found"

Make sure `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are in `backend/.env`

### "No tracks found for artist"

- Check artist name spelling
- Some artists may not have previews available
- Try a different artist

### "Failed to initialize Spotify API"

- Verify credentials are correct
- Check internet connection
- Spotify API may be temporarily unavailable

## Legal Notes

✅ **Legal:**
- Using Spotify's public 30-second previews
- Storing mathematical fingerprints (not audio)
- Deleting audio immediately after processing

❌ **Not Legal:**
- Downloading full songs
- Storing audio files permanently
- Redistributing copyrighted content

## Next Steps

1. **Run training** on your target artists
2. **Export fingerprints** for model training
3. **Train your model** using the fingerprints
4. **Integrate** with your fingerprint matching system

## API Reference

### `StreamingTrainer` Class

```python
trainer = StreamingTrainer(spotify_client_id, spotify_client_secret)

# Train on single artist
count = trainer.train_artist_from_spotify("Drake", max_tracks=50)

# Train on multiple artists
total = trainer.train_multiple_artists(
    ["Drake", "Travis Scott"],
    max_tracks_per_artist=50
)

# Save data
trainer.save_training_data("my_data.json")

# Load data
trainer.load_training_data("my_data.json")

# Export for training
data = trainer.export_for_model_training()
```
