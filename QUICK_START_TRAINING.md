# Quick Start: Automated Training

## 🚀 Get Running in 3 Steps

### ⚠️ Important: Spotify Premium Required

As of February 2026, **Development Mode apps require a Spotify Premium account**. Our trainer uses `GET /search` which is still available.

### Step 1: Get Spotify API Credentials

1. Go to: https://developer.spotify.com/dashboard
2. Click "Create an app"
3. Copy **Client ID** and **Client Secret**
4. **Note:** You need a Spotify Premium account for Development Mode

### Step 2: Add to Environment

Add to `backend/.env`:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### Step 3: Run Training

```bash
# Setup (first time only)
./scripts/setup_streaming_trainer.sh

# Run training
./scripts/run_streaming_trainer.sh
```

That's it! 🎉

## What Happens

1. ✅ Streams 30-second previews from Spotify (legal)
2. ✅ Generates fingerprints from each preview
3. ✅ Stores fingerprints only (not audio)
4. ✅ Deletes audio immediately
5. ✅ Saves to `data/training_fingerprints/`

## Custom Artists

```bash
./scripts/run_streaming_trainer.sh "Drake" "Travis Scott" "Metro Boomin"
```

## Check Results

```bash
ls -lh data/training_fingerprints/
```

## Next Steps

- Use fingerprints to train your model
- Add more artists
- Automate with cron (see `STREAMING_TRAINER.md`)

## Troubleshooting

**"ModuleNotFoundError: spotipy"**
```bash
./scripts/setup_streaming_trainer.sh
```

**"Spotify credentials not found"**
- Make sure `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are in `backend/.env`

**"No tracks found"**
- Check artist name spelling
- Some artists may not have previews available
