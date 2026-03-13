# Shadow PC Training Server Setup

This guide walks you through setting up your Shadow PC to receive training requests from your Type Beat app.

## Overview

The Shadow PC Training Server allows you to:
- Receive training requests from your Cloud Run backend
- Download YouTube audio without bot detection issues
- Generate audio fingerprints
- Upload results to Google Cloud Storage
- Avoid Cloud Run timeout issues

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Your App      │───────> │  Cloud Run      │───────> │  Shadow PC      │
│  (Frontend)     │ Trigger │   Backend       │ Webhook │   Training      │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │  YouTube        │
                                                         │  Downloads      │
                                                         └─────────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────────┐
                                                         │  Cloud Storage  │
                                                         │  Uploads        │
                                                         └─────────────────┘
```

## Prerequisites

1. **Shadow PC** with Windows or Linux
2. **Python 3.10+** installed
3. **Service account key** for Google Cloud Storage (already in repo: `shadow-pc-key.json`)
4. **Environment variables** from your Cloud Run backend

## Step 1: Prepare Your Shadow PC

### On Windows:
1. Install Python 3.10+ from https://python.org
2. Install Git from https://git-scm.com
3. Open PowerShell or Command Prompt

### On Linux:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

## Step 2: Copy Files to Shadow PC

### Option A: Using Git (Recommended)
```bash
# Clone your repository
git clone <your-repo-url>
cd Type beat/backend
```

### Option B: Manual Copy
1. Copy these files from your Mac to Shadow PC:
   - `backend/` folder (entire directory)
   - Make sure to include: `shadow-pc-key.json`

## Step 3: Run Setup Script

On your Shadow PC, in the backend directory:

```bash
# Windows PowerShell
.\setup_shadow_pc.sh

# Linux/Mac
bash setup_shadow_pc.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up Google Cloud credentials
- Create startup scripts

## Step 4: Configure Environment Variables

Create or edit the `.env` file in the backend directory:

```env
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/shadow-pc-key.json
FINGERPRINT_BUCKET_NAME=type-beat-fingerprints

# YouTube API (required for searching)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Spotify (optional - for additional previews)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Webhook Server Configuration
PORT=8000
```

### Getting Your YouTube API Key:
1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create credentials (API Key)
5. Copy the API key to your `.env` file

## Step 5: Start the Training Server

### Quick Start:
```bash
# Windows PowerShell
.\start_shadow_pc_server.sh

# Linux/Mac
bash start_shadow_pc_server.sh
```

### Manual Start:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/shadow-pc-key.json  # Linux/Mac
# or
set GOOGLE_APPLICATION_CREDENTIALS=%cd%\shadow-pc-key.json  # Windows

# Start server
python shadow_pc_webhook_server.py
```

The server will start on `http://0.0.0.0:8000`

## Step 6: Configure Cloud Run Backend

Update your Cloud Run backend environment variables:

1. Go to your Cloud Run service in Google Cloud Console
2. Click "Edit & Deploy New Revision"
3. Add these environment variables:
   - `SHADOW_PC_WEBHOOK_URL`: `http://YOUR_SHADOW_PC_IP:8000`
   - Replace `YOUR_SHADOW_PC_IP` with your Shadow PC's public IP

### Finding Your Shadow PC IP:
- **Windows**: Open Command Prompt and run `ipconfig`
- **Linux**: Open terminal and run `curl ifconfig.me`

### Port Forwarding (If behind router):
You may need to forward port 8000 on your router to your Shadow PC's local IP.

## Step 7: Test the Connection

### From your Mac/local machine:
```bash
# Test health endpoint
curl http://YOUR_SHADOW_PC_IP:8000/health

# Expected response:
# {"status":"healthy","timestamp":"..."}
```

### From Cloud Run backend:
The backend will automatically test the connection when you trigger training.

## Usage

### Trigger Training from Your App:

```javascript
// From your frontend app
const response = await fetch('https://your-backend-url/api/fingerprint/train', {
  method: 'POST',
  headers: { 'Content-Type': 'multipart/form-data' },
  body: formData
});
```

### Check Training Status:
```bash
curl https://your-backend-url/api/fingerprint/train/status
```

### Stop Training:
```bash
curl -X POST https://your-backend-url/api/fingerprint/train/stop
```

## Running as a System Service (Auto-start on boot)

### Windows:
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Shadow PC Training Server"
4. Trigger: At startup
5. Action: Start a program
   - Program: `python`
   - Arguments: `shadow_pc_webhook_server.py`
   - Start in: `C:\path\to\Type beat\backend`

### Linux:
```bash
# Install as systemd service
sudo mv shadow-pc-trainer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shadow-pc-trainer
sudo systemctl start shadow-pc-trainer

# Check status
sudo systemctl status shadow-pc-trainer
```

## Troubleshooting

### Server won't start:
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Kill existing process
taskkill /PID <PID> /F  # Windows
kill -9 <PID>  # Linux/Mac
```

### YouTube downloads failing:
- Check your `YOUTUBE_API_KEY` is valid
- Make sure you have internet connection
- Check Shadow PC logs for specific errors

### Cloud Storage upload failing:
```bash
# Verify credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test Cloud Storage connection
python -c "from google.cloud import storage; print(storage.Client().lookup_bucket('your-bucket'))"
```

### Connection timeout from Cloud Run:
- Check your Shadow PC public IP is correct
- Verify port 8000 is accessible from internet
- Check firewall settings on Shadow PC
- Try: `curl http://YOUR_SHADOW_PC_IP:8000/health` from Cloud Run

### View logs:
```bash
# Server logs are printed to console
# For more verbose logging, set environment variable:
export LOG_LEVEL=DEBUG
```

## Security Best Practices

1. **Firewall**: Only allow incoming connections on port 8000
2. **VPN**: Consider using a VPN for secure communication
3. **API Keys**: Never commit API keys to git
4. **Service Account**: The service account only needs Storage Object permissions

## Monitoring

### Check server health:
```bash
curl http://localhost:8000/health
```

### View training status:
```bash
curl http://localhost:8000/train/status
```

### Server metrics:
- Training progress: 0-100%
- Current artist being trained
- Total fingerprints generated
- Upload status to Cloud Storage

## Performance Tips

1. **SSD Storage**: Use SSD for faster temporary file operations
2. **CPU**: Training is CPU-intensive, more cores = faster
3. **RAM**: 8GB+ recommended for large training jobs
4. **Network**: Fast internet connection for YouTube downloads

## Next Steps

1. ✅ Server is running on Shadow PC
2. ✅ Cloud Run backend can reach Shadow PC
3. ✅ Test training with a single artist
4. ✅ Verify fingerprints are uploaded to Cloud Storage
5. ✅ Check fingerprints appear in your app

## Support

For issues:
1. Check server logs on Shadow PC
2. Check Cloud Run logs in Google Cloud Console
3. Test connection: `curl http://YOUR_SHADOW_PC_IP:8000/health`
4. Verify environment variables are set correctly

---

**🎉 You're all set!** Your Shadow PC is now ready to handle training requests from your Type Beat app!
