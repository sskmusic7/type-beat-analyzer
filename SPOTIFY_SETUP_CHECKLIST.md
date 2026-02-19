# Spotify API Setup Checklist

## ⏰ Timeline

- **February 11, 2026**: New Development Mode restrictions take effect
- **App creation may resume**: Check on/after February 11th

## ✅ Pre-Setup (Already Done)

- [x] Streaming trainer code created (`ml/streaming_trainer.py`)
- [x] Dependencies listed (`ml/requirements.txt`)
- [x] Run scripts created (`scripts/run_streaming_trainer.sh`)
- [x] Setup script created (`scripts/setup_streaming_trainer.sh`)
- [x] Documentation updated with API changes
- [x] Backend `.env` file exists

## 📋 When App Creation is Available (February 11+)

### Step 1: Create Spotify App

1. Go to: https://developer.spotify.com/dashboard
2. Click "Create app" (should be available after Feb 11)
3. Fill in:
   - **App name**: `Type Beat Trainer` (or your choice)
   - **App description**: `Automated training data collection for type beat classification`
   - **Website**: `http://localhost:3000` (optional)
   - **Redirect URI**: `http://127.0.0.1:3000/callback` (required - note: use 127.0.0.1, NOT localhost)
   - ✅ Check "I understand and agree to Spotify's Developer Terms of Service"
4. Click "Save"
5. **Copy your credentials:**
   - Client ID (visible immediately)
   - Client Secret (click "Show" to reveal)

### Step 2: Add Credentials to `.env`

Edit `backend/.env` and add:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

**Important:** Make sure you have a **Spotify Premium account** (required for Development Mode as of Feb 2026)

### Step 3: Install Dependencies

```bash
./scripts/setup_streaming_trainer.sh
```

Or manually:
```bash
cd ml
pip install spotipy requests python-dotenv faiss-cpu
```

### Step 4: Test the Setup

```bash
# Quick test (will fail without credentials, but checks imports)
cd ml
python -c "from streaming_trainer import StreamingTrainer; print('✅ Import successful')"
```

### Step 5: Run Training

```bash
# Run with default artists
./scripts/run_streaming_trainer.sh

# Or with custom artists
./scripts/run_streaming_trainer.sh "Drake" "Travis Scott" "Metro Boomin"
```

## 🔍 Verification Steps

After setup, verify:

1. **Credentials are set:**
   ```bash
   grep SPOTIFY backend/.env
   ```

2. **Dependencies installed:**
   ```bash
   python -c "import spotipy, requests; print('✅ Dependencies OK')"
   ```

3. **Test search (requires credentials):**
   ```bash
   cd ml
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv('../backend/.env')
   import spotipy
   from spotipy.oauth2 import SpotifyClientCredentials
   
   client_id = os.getenv('SPOTIFY_CLIENT_ID')
   client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
   
   if client_id and client_secret:
       creds = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
       sp = spotipy.Spotify(client_credentials_manager=creds)
       results = sp.search(q='artist:Drake', type='track', limit=1)
       print('✅ Spotify API connection successful!')
       print(f'   Found {len(results[\"tracks\"][\"items\"])} track(s)')
   else:
       print('❌ Credentials not found in .env')
   "
   ```

## 🚨 Troubleshooting

### "App creation is blocked"
- Wait until after February 11, 2026
- Check: https://developer.spotify.com/blog for updates

### "Spotify Premium required"
- You need a Premium account for Development Mode apps
- This is a new requirement as of February 2026

### "ModuleNotFoundError: spotipy"
```bash
./scripts/setup_streaming_trainer.sh
```

### "Invalid client credentials"
- Double-check Client ID and Client Secret in `backend/.env`
- Make sure there are no extra spaces or quotes
- Regenerate credentials if needed

### "No tracks found"
- Check artist name spelling
- Some artists may not have previews available
- Try a different artist

## 📚 Resources

- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- [Spotify API Changes - February 2026](https://developer.spotify.com/documentation/web-api/references/changes/february-2026)
- [Spotify Developer Access Update](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security)
- [Web API Documentation](https://developer.spotify.com/documentation/web-api)

## ✅ Quick Command Reference

```bash
# Setup (first time)
./scripts/setup_streaming_trainer.sh

# Run training
./scripts/run_streaming_trainer.sh

# Check credentials
grep SPOTIFY backend/.env

# Test API connection (after credentials added)
cd ml && python -c "from streaming_trainer import StreamingTrainer; import os; from dotenv import load_dotenv; load_dotenv('../backend/.env'); t = StreamingTrainer(os.getenv('SPOTIFY_CLIENT_ID'), os.getenv('SPOTIFY_CLIENT_SECRET')); print('✅ Trainer initialized')"
```
