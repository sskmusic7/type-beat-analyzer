# Shadow PC Integration - Complete Setup

## What Was Created

### 1. Webhook Server (`shadow_pc_webhook_server.py`)
- FastAPI server that runs on your Shadow PC
- Receives training requests from Cloud Run backend
- Handles YouTube downloads and fingerprint generation
- Uploads results to Google Cloud Storage

### 2. Updated Trainer (`ml/hybrid_trainer.py`)
- Added status tracking for progress monitoring
- Integrated Cloud Storage uploads
- Added async training method for webhook server
- Can stop training mid-process

### 3. Setup Script (`setup_shadow_pc.sh`)
- Automated setup for Shadow PC environment
- Installs dependencies
- Configures Google Cloud credentials
- Creates systemd service file

### 4. Documentation
- `SHADOW_PC_SETUP.md` - Complete setup guide
- `SHADOW_PC_QUICKSTART.md` - Quick reference

## How It Works

```
User triggers training
    ↓
Frontend app → Cloud Run Backend
    ↓
Cloud Run → Shadow PC Webhook (HTTP POST)
    ↓
Shadow PC downloads from YouTube
    ↓
Generates fingerprints
    ↓
Uploads to Cloud Storage
    ↓
Cloud Run reads from Cloud Storage
    ↓
Fingerprints available in app
```

## Required Files on Shadow PC

Copy these to your Shadow PC's `backend/` directory:

```
backend/
├── shadow_pc_webhook_server.py      # NEW - Webhook server
├── ml/
│   └── hybrid_trainer.py            # UPDATED - With Cloud Storage
├── app/
│   └── fingerprint_service_cloud_storage.py  # Already exists
├── shadow-pc-key.json               # Already exists
├── .env                             # Already exists (add vars)
├── requirements.txt                 # Already exists
└── setup_shadow_pc.sh               # NEW - Setup script
```

## Environment Variables

Add these to your `.env` file on Shadow PC:

```env
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/shadow-pc-key.json
FINGERPRINT_BUCKET_NAME=type-beat-fingerprints

# YouTube (REQUIRED)
YOUTUBE_API_KEY=your_youtube_api_key

# Spotify (Optional - for additional previews)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Server
PORT=8000
```

## Cloud Run Configuration

Add this environment variable to your Cloud Run service:

```env
SHADOW_PC_WEBHOOK_URL=http://YOUR_SHADOW_PC_PUBLIC_IP:8000
```

## Setup Steps

### Step 1: Copy to Shadow PC
```bash
# From your Mac
scp -r "/Users/sskmusic/Type beat/backend" user@shadow-pc-ip:~/
```

### Step 2: Run Setup on Shadow PC
```bash
cd backend
bash setup_shadow_pc.sh
```

### Step 3: Start Server
```bash
bash start_shadow_pc_server.sh
```

### Step 4: Get Shadow PC IP
```bash
curl ifconfig.me
```

### Step 5: Update Cloud Run
In Google Cloud Console, update `SHADOW_PC_WEBHOOK_URL` with your Shadow PC IP

### Step 6: Test
```bash
# From your Mac
curl http://YOUR_SHADOW_PC_IP:8000/health
```

## API Endpoints

### On Shadow PC (port 8000):

- `GET /` - Server info
- `GET /health` - Health check
- `POST /train/start` - Start training
- `GET /train/status` - Get training status
- `POST /train/stop` - Stop training

### On Cloud Run Backend:

- `POST /api/fingerprint/train` - Trigger training (forwards to Shadow PC)
- `GET /api/fingerprint/train/status` - Get status (from Shadow PC)
- `POST /api/fingerprint/train/stop` - Stop training (on Shadow PC)

## Benefits

1. ✅ **No more timeouts** - Shadow PC has no time limits
2. ✅ **YouTube works** - No bot detection on residential connection
3. ✅ **More storage** - Shadow PC has local disk space
4. ✅ **Persistent storage** - Results go to Cloud Storage
5. ✅ **Progress tracking** - Real-time status updates

## Security Notes

1. Shadow PC service account has limited permissions (Storage only)
2. Webhook URL should be protected or use VPN
3. Consider adding authentication to webhook server
4. Firewall should only allow port 8000 from Cloud Run IPs

## Monitoring

### Check Shadow PC server:
```bash
curl http://YOUR_SHADOW_PC_IP:8000/train/status
```

### Check Cloud Run logs:
In Google Cloud Console → Cloud Run → Logs

### Expected response from status endpoint:
```json
{
  "is_training": true,
  "status": "training",
  "progress": 50,
  "message": "Training on Artist Name (2/4)",
  "current_artist": "Artist Name",
  "total_artists": 4,
  "completed_artists": 2,
  "timestamp": "2026-03-13T..."
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Server won't start | Check port 8000 not in use: `lsof -i :8000` |
| Can't connect from Cloud Run | Check firewall, verify IP, test health endpoint |
| YouTube downloads fail | Check YOUTUBE_API_KEY in .env |
| Cloud Storage upload fails | Verify shadow-pc-key.json and bucket permissions |
| Training not starting | Check Shadow PC logs, verify .env variables |

## Next Steps

1. ✅ Copy files to Shadow PC
2. ✅ Run setup script
3. ✅ Start webhook server
4. ✅ Update Cloud Run environment
5. ✅ Test with single artist
6. ✅ Verify fingerprints in Cloud Storage
7. ✅ Test full training from app

## File Locations

### On Your Mac:
- `/Users/sskmusic/Type beat/backend/`

### On Shadow PC (after copy):
- `~/backend/` or wherever you copied it

## Support

For detailed setup instructions, see:
- `SHADOW_PC_SETUP.md` - Complete guide
- `SHADOW_PC_QUICKSTART.md` - Quick reference

---

**🎉 Your Shadow PC is now ready to handle training!**
