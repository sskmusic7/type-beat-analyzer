# Session Memory: Shadow PC Training Integration

**Date:** March 13, 2026
**Goal:** Set up Shadow PC to handle training requests from the Type Beat app to avoid Cloud Run timeouts and YouTube bot detection

---

## Problem Statement

The Type Beat app was experiencing issues when triggering training:
1. **Cloud Run timeouts** - Training took longer than 60 minutes (Cloud Run max timeout)
2. **YouTube bot detection** - yt-dlp downloads were being blocked on Cloud Run IP addresses
3. **No progress tracking** - Couldn't monitor training progress in real-time

## Solution Implemented

Created a Shadow PC webhook server that:
- Receives training requests from Cloud Run backend
- Downloads YouTube audio from residential connection (no bot detection)
- Generates audio fingerprints locally
- Uploads results to Google Cloud Storage
- Provides real-time status updates

---

## Files Created (8 new files)

### 1. `backend/shadow_pc_webhook_server.py`
**Purpose:** FastAPI server that runs on Shadow PC to handle training requests

**Key Features:**
- Listens on port 8000 for webhook requests
- Endpoints:
  - `GET /` - Server info
  - `GET /health` - Health check
  - `POST /train/start` - Start training
  - `GET /train/status` - Get training status
  - `POST /train/stop` - Stop training
- Manages training lifecycle
- Returns real-time progress updates

**Code Location:** `/Users/sskmusic/Type beat/backend/shadow_pc_webhook_server.py`

### 2. `backend/setup_shadow_pc.sh`
**Purpose:** Automated setup script for Shadow PC environment

**What it does:**
- Creates Python virtual environment
- Installs dependencies (FastAPI, uvicorn, httpx, etc.)
- Sets up Google Cloud credentials
- Creates systemd service file
- Creates startup script
- Checks required environment variables

**Usage:**
```bash
cd backend
bash setup_shadow_pc.sh
```

**Code Location:** `/Users/sskmusic/Type beat/backend/setup_shadow_pc.sh`

### 3. `backend/app/training_service_shadow_pc.py`
**Purpose:** Client that runs on Cloud Run to communicate with Shadow PC

**Key Features:**
- Sends HTTP requests to Shadow PC webhook server
- Methods:
  - `check_shadow_pc_health()` - Health check
  - `start_training(artists, max_per_artist, clear_existing)` - Trigger training
  - `get_training_status()` - Get status updates
  - `stop_training()` - Stop training

**Configuration:**
- Uses `SHADOW_PC_WEBHOOK_URL` environment variable
- Default: `http://46.247.137.210:8000`

**Code Location:** `/Users/sskmusic/Type beat/backend/app/training_service_shadow_pc.py`

### 4. `backend/app/fingerprint_service_cloud_storage.py`
**Purpose:** Handles Cloud Storage uploads from Shadow PC

**Classes:**
- `CloudStorageFingerprintService` - Manages fingerprints in Cloud Storage
- `CloudStorageUploader` - Uploads training results

**Key Methods:**
- `upload_training_results(fingerprint_data, index_path, metadata_path)`
- Uploads individual fingerprint embeddings as .npz files
- Uploads FAISS index
- Uploads metadata JSON
- Creates upload logs

**Code Location:** `/Users/sskmusic/Type beat/backend/app/fingerprint_service_cloud_storage.py`

### 5. `backend/ml/hybrid_trainer.py` (Updated)
**Purpose:** Enhanced trainer with Cloud Storage integration and status tracking

**New Features:**
- Status tracking (progress %, current artist, completed count)
- Async training method `train_from_youtube()`
- Cloud Storage upload after each artist
- Stop training capability
- Integration with CloudStorageUploader

**Key Methods Added:**
- `get_status()` - Returns current training status
- `update_status()` - Updates status
- `stop_training()` - Stops training
- `train_from_youtube()` - Async training for webhook server

**Code Location:** `/Users/sskmusic/Type beat/backend/ml/hybrid_trainer.py`

### 6. `backend/SHADOW_PC_SETUP.md`
**Purpose:** Complete setup guide for Shadow PC

**Contents:**
- Architecture overview
- Prerequisites
- Step-by-step setup instructions
- Environment configuration
- Usage examples
- Troubleshooting guide
- Security best practices
- Performance tips

**Code Location:** `/Users/sskmusic/Type beat/backend/SHADOW_PC_SETUP.md`

### 7. `backend/SHADOW_PC_QUICKSTART.md`
**Purpose:** Quick reference for setting up Shadow PC

**Contents:**
- Minimal steps to get running
- File checklist
- Environment variables needed
- Common troubleshooting

**Code Location:** `/Users/sskmusic/Type beat/backend/SHADOW_PC_QUICKSTART.md`

### 8. `backend/README_SHADOW_PC_INTEGRATION.md`
**Purpose:** Integration overview and documentation

**Contents:**
- What was created
- How it works (flow diagram)
- Required files
- Environment variables
- API endpoints
- Benefits
- Security notes

**Code Location:** `/Users/sskmusic/Type beat/README_SHADOW_PC_INTEGRATION.md`

---

## Files Modified

### `backend/main.py`
**Changes:**
- Already had Shadow PC integration (lines 742-761)
- Uses `training_service_shadow_pc.py` for training
- Endpoints:
  - `POST /api/fingerprint/train` - Triggers training on Shadow PC
  - `GET /api/fingerprint/train/status` - Gets status from Shadow PC
  - `POST /api/fingerprint/train/stop` - Stops training on Shadow PC

---

## Architecture Flow

```
User triggers training in app
        ↓
Frontend sends POST to Cloud Run /api/fingerprint/train
        ↓
Cloud Run backend sends POST to Shadow PC /train/start
        ↓
Shadow PC webhook server receives request
        ↓
HybridTrainer downloads from YouTube (no bot detection!)
        ↓
Generates audio fingerprints
        ↓
Uploads to Google Cloud Storage
        ↓
Cloud Run reads from Cloud Storage
        ↓
Results available in app
```

---

## Environment Variables Needed

### On Shadow PC (in `.env`):
```env
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/shadow-pc-key.json
FINGERPRINT_BUCKET_NAME=type-beat-fingerprints

# YouTube (REQUIRED)
YOUTUBE_API_KEY=your_youtube_api_key

# Spotify (Optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Server
PORT=8000
```

### On Cloud Run:
```env
SHADOW_PC_WEBHOOK_URL=http://YOUR_SHADOW_PC_PUBLIC_IP:8000
```

---

## Git Commit Information

**Commit Hash:** 9493bb0
**Commit Message:** "Add Shadow PC training server integration"
**Branch:** main
**Remote:** https://github.com/sskmusic7/type-beat-analyzer.git

**Files Committed:**
- backend/shadow_pc_webhook_server.py (new)
- backend/setup_shadow_pc.sh (new)
- backend/app/training_service_shadow_pc.py (new)
- backend/app/fingerprint_service_cloud_storage.py (new)
- backend/ml/hybrid_trainer.py (new, forced add from .gitignore)
- backend/SHADOW_PC_SETUP.md (new)
- backend/SHADOW_PC_QUICKSTART.md (new)
- backend/README_SHADOW_PC_INTEGRATION.md (new)

---

## How to Use This Memory

### To Set Up Shadow PC (First Time):

1. **Clone repository on Shadow PC:**
   ```bash
   git clone https://github.com/sskmusic7/type-beat-analyzer.git
   cd type-beat-analyzer/backend
   ```

2. **Run setup script:**
   ```bash
   bash setup_shadow_pc.sh
   ```

3. **Configure environment:**
   - Copy `shadow-pc-key.json` to backend folder
   - Create `.env` file with API keys
   - See SHADOW_PC_QUICKSTART.md for required variables

4. **Start server:**
   ```bash
   bash start_shadow_pc_server.sh
   ```

5. **Get Shadow PC IP:**
   ```bash
   curl ifconfig.me
   ```

6. **Update Cloud Run:**
   - Go to Google Cloud Console
   - Edit Cloud Run service
   - Add `SHADOW_PC_WEBHOOK_URL=http://YOUR_IP:8000`

### To Update Shadow PC (After Code Changes):

```bash
cd type-beat-analyzer
git pull origin main
cd backend
# Restart server if running
```

### To Trigger Training from App:

```javascript
// Frontend code
const response = await fetch('https://your-backend-url/api/fingerprint/train', {
  method: 'POST',
  headers: { 'Content-Type': 'multipart/form-data' },
  body: formData
});
```

### To Check Training Status:

```bash
curl https://your-backend-url/api/fingerprint/train/status
```

**Expected Response:**
```json
{
  "is_training": true,
  "status": "training",
  "progress": 50,
  "message": "Training on Artist Name (2/4)",
  "current_artist": "Artist Name",
  "total_artists": 4,
  "completed_artists": 2,
  "timestamp": "2026-03-13T...",
  "source": "shadow_pc"
}
```

---

## Key Benefits

1. ✅ **No Timeouts** - Shadow PC has no time limits (unlike Cloud Run's 60 min max)
2. ✅ **YouTube Works** - Residential IP, no bot detection
3. ✅ **More Storage** - Shadow PC has local disk space
4. ✅ **Persistent** - Results stored in Cloud Storage
5. ✅ **Progress Tracking** - Real-time status updates
6. ✅ **Easy to Update** - Just `git pull` on Shadow PC

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Server won't start | Check port 8000: `lsof -i :8000` (Mac/Linux) or `netstat -ano \| findstr :8000` (Windows) |
| Can't connect from Cloud Run | Verify IP: `curl ifconfig.me` on Shadow PC, test health endpoint |
| YouTube downloads fail | Check `YOUTUBE_API_KEY` in `.env` file |
| Cloud Storage upload fails | Verify `shadow-pc-key.json` exists and bucket permissions |
| Training not starting | Check Shadow PC logs, verify all env variables set |

---

## Service Account Key Location

**File:** `backend/shadow-pc-key.json`
**Service Account:** `shadow-pc-trainer@eminent-century-464801-b0.iam.gserviceaccount.com`
**Purpose:** Allows Shadow PC to upload fingerprints to Cloud Storage

⚠️ **Security Note:** This file contains credentials. It's in the repo but should be:
- Added to .gitignore in future
- Or use git-secrets / git-crypt
- Or set up as a secret in GitHub

---

## Future Improvements

1. **Authentication** - Add API key authentication to webhook server
2. **VPN Tunnel** - Use Cloud SQL or Cloud VPN for secure connection
3. **Auto-restart** - Configure systemd service for auto-start on boot
4. **Monitoring** - Add Prometheus metrics for training progress
5. **Multiple Shadow PCs** - Load balance across multiple machines
6. **Queue System** - Add Redis queue for multiple training jobs

---

## Related Documentation Files

- `backend/SHADOW_PC_SETUP.md` - Complete setup guide
- `backend/SHADOW_PC_QUICKSTART.md` - Quick reference
- `backend/README_SHADOW_PC_INTEGRATION.md` - Integration overview
- `backend/shadow_pc_webhook_server.py` - Server code with inline comments
- `backend/ml/hybrid_trainer.py` - Trainer with Cloud Storage integration

---

## Session Summary

**What We Did:**
1. Created Shadow PC webhook server to receive training requests
2. Enhanced trainer with Cloud Storage upload and status tracking
3. Created automated setup script for easy deployment
4. Created comprehensive documentation
5. Committed and pushed all changes to GitHub

**Why We Did It:**
- Solve Cloud Run timeout issues
- Fix YouTube bot detection problems
- Enable long-running training jobs
- Provide real-time progress tracking

**Result:**
- Shadow PC can now handle all training
- App can trigger training on demand
- Results automatically sync to Cloud Storage
- Easy to update via git pull

---

**End of Session Memory**

Created: March 13, 2026
Last Updated: March 13, 2026
Status: Complete and deployed to GitHub
